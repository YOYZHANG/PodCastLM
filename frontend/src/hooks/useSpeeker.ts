import { useCallback, useEffect, useState } from 'react';
import { BASE_URL } from '@/lib/constant';
type SPEEKERS = Record<string, Array<{ id: string, name: string }>>

export function useSpeeker() {
  const [data, setData] = useState<SPEEKERS | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [provider, setProvider] = useState<string>();
  const [hostVoice, setHostVoice] = useState<string>();
  const [guestVoice, setGuestVoice] = useState<string>();

  const load = useCallback(async () => {
    setIsLoading(true);
    setData(null);
    setError(null);

    try {
      const response = await fetch(BASE_URL + "/speekers");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const jsonData = await response.json();
      setData(jsonData);
      const defaultProvider = Object.keys(jsonData)[0];
      setProvider(defaultProvider)
      defaultProvider && setHostVoice(jsonData[defaultProvider][0].id)
      defaultProvider && setGuestVoice(jsonData[defaultProvider][1].id)
    } catch (error) {
      setError('获取数据时发生错误: ' + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { load() }, [load])

  return {
    data,
    hostVoice, setHostVoice,
    guestVoice, setGuestVoice,
    provider, setProvider,
    error, isLoading, load, 
  };
}
