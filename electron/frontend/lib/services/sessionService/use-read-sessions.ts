import { useState, useEffect } from 'react';
import axios from 'axios';
import { useBackendUrl } from '@/contexts/BackendUrlContext';

const useReadSessions = () => {
    const backendUrl = useBackendUrl()
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [sessions, setSessions] = useState([]);

    // Function to fetch session keys
    const fetchSessions = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${backendUrl}/session`);
            setSessions(response.data);  // Assuming the backend returns an array of session keys
        } catch (err) {
            setError(err.message || 'Unknown error');
            setSessions([]);  // Reset session keys on error
        }
        setLoading(false);
    };

    // Effect to fetch sessions when the hook is used
    useEffect(() => {
        fetchSessions();
    }, []);  // Empty dependency array to run only once after the component mounts

    return { sessions, loading, error, refreshSessions: fetchSessions };
};

export default useReadSessions;
