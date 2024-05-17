import { useState } from 'react';
import axios from 'axios';
import { useBackendUrl } from '@/contexts/BackendUrlContext';

const useDeleteSession = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [response, setResponse] = useState(null);

    // Function to delete a session
    // Note: session is the session id
    const deleteSession = async (session) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.delete(`${backendUrl}/session`, { params: { session } });
            setResponse(response.data);  // Save the response data which might be the updated session list
        } catch (err) {
            setError(err.message || 'Unknown error');
        }
        setLoading(false);
    };

    return { deleteSession, response, loading, error };
};

export default useDeleteSession;
