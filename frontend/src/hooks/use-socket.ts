import { useEffect, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuditStore } from '../store/useAuditStore';

let socket: Socket | null = null;

export const useSocket = () => {
  const { setActiveAudit, pollAuditStatus } = useAuditStore();

  const connect = useCallback(() => {
    if (socket?.connected) return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
    socket = io(wsUrl, {
      transports: ['websocket'],
      reconnectionAttempts: 5,
    });

    socket.on('connect', () => {
      console.log('WebSocket Connected');
    });

    socket.on('audit_update', (data) => {
      console.log('Audit Update:', data);
      setActiveAudit(data);
    });

    socket.on('audit_completed', (data) => {
      console.log('Audit Completed:', data);
      pollAuditStatus(data.audit_id);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket Disconnected');
    });
  }, [setActiveAudit, pollAuditStatus]);

  const disconnect = useCallback(() => {
    if (socket) {
      socket.disconnect();
      socket = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      // Logic to decide if we should disconnect on unmount
    };
  }, [connect]);

  return { socket, connect, disconnect };
};
