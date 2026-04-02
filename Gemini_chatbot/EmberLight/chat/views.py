from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatLog
from .serializers import ChatLogSerializer, ChatSessionSerializer
from journal.models import JournalEntry
from .utils import send_message_with_history
from datetime import datetime, timedelta

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    serializer = ChatSessionSerializer(sessions, many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_chat_session(request):
    title = request.data.get("title", "New chat")
    session = ChatSession.objects.create(user=request.user, title=title)
    return Response({"id": session.id, "title": session.title})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_session_history(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
        logs = ChatLog.objects.filter(session=session).order_by("timestamp")
        serializer = ChatLogSerializer(logs, many=True)
        return Response({"logs": serializer.data})
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    message = request.data.get("message")
    if not message:
        return Response({"error": "Message is required"}, status=400)

    # Últimos 10 mensajes del historial guardado en BD
    previous_logs = ChatLog.objects.filter(session=session).order_by("timestamp")[:10]
    chat_history = []
    for log in previous_logs:
        chat_history.append({"role": "user",  "parts": log.message})
        chat_history.append({"role": "model", "parts": log.response})

    # Entradas de diario de la última semana
    date_from = datetime.now() - timedelta(days=7)
    journal_entries = JournalEntry.objects.filter(
        user=request.user,
        date__gte=date_from
    ).order_by("-date")

    journal_context = "Entradas del diario (última semana):\n" + "\n".join(
        f"{entry.date}: {entry.mood} - {entry.text}"
        for entry in journal_entries
    )

    try:
        ai_response = send_message_with_history(chat_history, journal_context, message)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    chat_log = ChatLog.objects.create(
        session=session,
        message=message,
        response=ai_response
    )
    chat_log.context_entries.set(journal_entries)

    return Response({"response": ai_response})

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_chat_session(request, session_id):
    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
        session.delete()
        return Response({"status": "success"})
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)
