// frontend/src/components/Layout/Layout.tsx
import React, { ReactNode } from 'react';
import { Container } from '@mui/material';
import { useLocation } from 'react-router-dom';
import Navbar from './Navbar';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';

  // Don't show navbar and container on landing page
  if (isLandingPage) {
    return <>{children}</>;
  }

  return (
    <>
      <Navbar />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {children}
      </Container>
    </>
  );
};

export default Layout;