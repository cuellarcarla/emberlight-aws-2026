import { createContext, useContext, useState, useEffect } from "react";
import { getCookie } from "../utils/cookies";

const AuthContext = createContext();
const API_BASE_URL = "https://emberlight.mehdi.cat";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/csrf/`, {
      credentials: 'include'
    });
  }, []);

  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/me/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: "include",
      });
      if (res.ok) {
        const userData = await res.json();
        setUser({
          id: userData.id,
          username: userData.username,
          email: userData.email,
        });
        return true;
      }
      setUser(null);
      return false;
    } catch (err) {
      setUser(null);
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async ({ username, password }) => {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Invalid username or password.");
    }

    const success = await fetchUser();
    if (!success) throw new Error("Session verification failed");
  };

  const logout = async () => {
    await fetch(`${API_BASE_URL}/auth/logout/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: "include",
    });
    setUser(null);
  };

  const register = async ({ username, email, password }) => {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      credentials: "include",
      body: JSON.stringify({ username, email, password }),
    });

    const responseData = await response.json();
    if (!response.ok) {
      const error = new Error(responseData.errors ? "Validation error" : "Registration failed");
      error.response = { data: responseData };
      throw error;
    }
    return responseData;
  };

  const updateUser = async ({ username, email }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/users/${user.id}/update/`, {
        method: 'PUT',
        headers: { 
          "Content-Type": "application/json",
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: "include",
        body: JSON.stringify({ username, email }),
      });

      const responseData = await response.json();

      if (!response.ok) {
        const errorMsg = responseData.errors 
          ? Object.values(responseData.errors).join('\n')
          : responseData.error || "Update failed";
        throw new Error(errorMsg);
      }

      setUser(prev => ({ ...prev, ...responseData }));
      return true;
    } catch (error) {
      console.error('Update error:', error);
      throw error;
    }
  };

  const deleteUserData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/users/delete-data/`, {
        method: 'POST',
        headers: { 
          "Content-Type": "application/json",
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error('Failed to delete user data');
      }
      return true;
    } catch (error) {
      console.error('Data deletion error:', error);
      throw error;
    }
  };

  // NUEVO: Eliminar cuenta de usuario
  const deleteUser = async () => {
    try {
      const response = await fetch(`https://emberlight.mehdi.cat/auth/users/${user.id}/delete/`, {
        method: 'DELETE',
        headers: { 
          "Content-Type": "application/json",
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error('Failed to delete user account');
      }
      setUser(null);
      return true;
    } catch (error) {
      console.error('Account deletion error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      logout,
      register,
      updateUser,
      deleteUserData,
      deleteUser, // <-- Añadido aquí
      loading
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
