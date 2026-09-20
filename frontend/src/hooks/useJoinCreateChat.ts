import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { JoinChatForm, ChatUserSession } from '../types';
import { joinRoomApi, createRoomApi } from '../services/RoomService';

export const useJoinCreateChat = () => {
  const [detail, setDetail] = useState<JoinChatForm>({
    roomId: '',
    userName: '',
  });
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDetail((prev) => ({
      ...prev,
      [name]: value,
    }));
    if (errorMessage) setErrorMessage('');
    if (successMessage) setSuccessMessage('');
  };

  const validate = (): boolean => {
    if (!detail.userName.trim() || !detail.roomId.trim()) {
      setErrorMessage('Vui lòng nhập đầy đủ Tên của bạn và Mã phòng (Room ID).');
      return false;
    }
    return true;
  };

  const saveUserSession = (roomData: any) => {
    const sessionData: ChatUserSession = {
      userName: detail.userName.trim(),
      roomId: detail.roomId.trim(),
      room: roomData,
    };
    sessionStorage.setItem('chat_user', JSON.stringify(sessionData));
  };

  const handleJoinChat = async () => {
    if (!validate()) return;

    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const roomData = await joinRoomApi(detail.roomId);
      saveUserSession(roomData);
      setSuccessMessage('Vào phòng thành công!');
      navigate('/chat');
    } catch (err: any) {
      console.error('Lỗi khi vào phòng:', err);
      setErrorMessage(err?.message || 'Không thể kết nối đến server backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async () => {
    if (!validate()) return;

    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const roomData = await createRoomApi(detail.roomId);
      saveUserSession(roomData);
      setSuccessMessage('Tạo phòng thành công!');
      navigate('/chat');
    } catch (err: any) {
      console.error('Lỗi khi tạo phòng:', err);
      setErrorMessage(err?.message || 'Không thể kết nối đến server backend.');
    } finally {
      setLoading(false);
    }
  };

  return {
    detail,
    errorMessage,
    successMessage,
    loading,
    handleInputChange,
    handleJoinChat,
    handleCreateRoom,
  };
};
