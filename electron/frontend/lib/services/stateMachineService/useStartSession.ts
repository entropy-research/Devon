import { useState } from 'react';
import { useSessionMachine } from './stateMachineService';

export const useStartSession = () => {
  const [sessionService, setSessionService] = useState<any>(null);

  const startSession = (port: number, name: string, path: string) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { state, service } = useSessionMachine({ port, name, path });
    setSessionService(service);
  };

  return { sessionService, startSession };
};