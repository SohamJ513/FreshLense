// frontend/src/components/Layout/LogoutModal.tsx
import React from 'react';

interface LogoutModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const LogoutModal: React.FC<LogoutModalProps> = ({ isOpen, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }} onClick={onCancel}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '400px',
        width: '90%',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
      }} onClick={e => e.stopPropagation()}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '1.5rem' }}>Confirm Logout</h2>
        <p style={{ margin: '0 0 8px 0', color: '#666' }}>Are you sure you want to log out?</p>
        <p style={{ margin: '0 0 24px 0', color: '#999', fontSize: '0.9rem' }}>
          You'll need to log in again to access your account.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button onClick={onCancel} style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #ddd',
            background: 'white',
            cursor: 'pointer'
          }}>
            Cancel
          </button>
          <button onClick={onConfirm} style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: '#dc2626',
            color: 'white',
            cursor: 'pointer'
          }}>
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogoutModal;