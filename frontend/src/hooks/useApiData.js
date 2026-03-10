import { useState, useEffect } from 'react';
import api from './api';

const REFRESH_INTERVAL = parseInt(import.meta.env.VITE_REFRESH_INTERVAL || '1800000'); // 30 mins

export const useApiData = (endpoint, params = {}, defaultData = null) => {
  const [data, setData] = useState(defaultData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    let timer;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(endpoint, { params });
        if (isMounted) setData(response.data);
      } catch (err) {
        if (isMounted) {
          console.error(`Error fetching ${endpoint}:`, err);
          setError(err.message || 'An error occurred');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    timer = setInterval(fetchData, REFRESH_INTERVAL);

    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, JSON.stringify(params)]);

  return { data, loading, error };
};