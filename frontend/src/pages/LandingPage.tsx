// src/pages/LandingPage.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  alpha,
  useTheme,
  Fade,
  Slide,
  Zoom,
} from '@mui/material';
import {
  VerifiedUser,
  CompareArrows,
  Monitor,
  RocketLaunch,
  Security,
  Analytics,
  Speed,
  CheckCircle,
  ArrowForward,
  Star,
  TrendingUp,
  Shield,
} from '@mui/icons-material';

const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const theme = useTheme();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: <VerifiedUser sx={{ fontSize: 36 }} />,
      title: 'Advanced Fact Checking',
      description: 'Advanced algorithms verify claims and technical information with 85% accuracy.',
      color: theme.palette.primary.main,
    },
    {
      icon: <CompareArrows sx={{ fontSize: 36 }} />,
      title: 'Version Comparison',
      description: 'Visual diff tools to track every change between content versions with precision.',
      color: theme.palette.secondary.main,
    },
    {
      icon: <Monitor sx={{ fontSize: 36 }} />,
      title: 'Real-time Monitoring',
      description: '24/7 automated monitoring with instant notifications for content changes.',
      color: theme.palette.success.main,
    },
    {
      icon: <Security sx={{ fontSize: 36 }} />,
      title: 'Content Integrity',
      description: 'Ensure your technical documentation and blogs remain accurate and reliable.',
      color: theme.palette.warning.main,
    },
    {
      icon: <Analytics sx={{ fontSize: 36 }} />,
      title: 'Smart Analytics',
      description: 'Detailed insights and reports on content changes and verification results.',
      color: theme.palette.info.main,
    },
    {
      icon: <Speed sx={{ fontSize: 36 }} />,
      title: 'Lightning Fast',
      description: 'Process and analyze content changes in seconds, not hours.',
      color: theme.palette.error.main,
    },
  ];

  const stats = [
    { number: '85%', label: 'Accuracy Rate', icon: <Star /> },
    { number: '24/7', label: 'Monitoring', icon: <Monitor /> },
    { number: '< 5s', label: 'Response Time', icon: <Speed /> },
    { number: '1000+', label: 'Websites Tracked', icon: <TrendingUp /> },
  ];

  return (
    <Box sx={{ overflow: 'hidden' }}>
      {/* Navigation */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          background: alpha(theme.palette.background.paper, 0.8),
          backdropFilter: 'blur(20px)',
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              py: 2,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '1.2rem',
                }}
              >
                FL
              </Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                }}
              >
                FreshLense
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {isAuthenticated ? (
                <Button
                  component={Link}
                  to="/dashboard"
                  variant="contained"
                  startIcon={<ArrowForward />}
                  sx={{
                    borderRadius: 3,
                    px: 3,
                    py: 1,
                  }}
                >
                  Go to Dashboard
                </Button>
              ) : (
                <>
                  <Button
                    component={Link}
                    to="/login"
                    variant="text"
                    sx={{
                      borderRadius: 3,
                      px: 3,
                      py: 1,
                    }}
                  >
                    Sign In
                  </Button>
                  <Button
                    component={Link}
                    to="/register"
                    variant="contained"
                    startIcon={<RocketLaunch />}
                    sx={{
                      borderRadius: 3,
                      px: 3,
                      py: 1,
                    }}
                  >
                    Get Started
                  </Button>
                </>
              )}
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Hero Section - COMPACT VERSION */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          color: 'white',
          minHeight: '85vh',
          display: 'flex',
          alignItems: 'center',
          position: 'relative',
          overflow: 'hidden',
          pt: 6,
        }}
      >
        {/* Animated Background Elements - Smaller */}
        <Box
          sx={{
            position: 'absolute',
            top: '20%',
            left: '10%',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${alpha(theme.palette.primary.light, 0.3)} 0%, transparent 70%)`,
            animation: 'float 8s ease-in-out infinite',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: '10%',
            right: '15%',
            width: 150,
            height: 150,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${alpha(theme.palette.secondary.light, 0.2)} 0%, transparent 70%)`,
            animation: 'float 6s ease-in-out infinite 1s',
          }}
        />

        <Container maxWidth="lg">
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' },
              alignItems: 'center',
              gap: 4,
            }}
          >
            <Slide in={isVisible} direction="right" timeout={800}>
              <Box sx={{ flex: 1 }}>
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 800,
                    fontSize: { xs: '2.5rem', md: '3rem', lg: '3.5rem' },
                    lineHeight: 1.2,
                    mb: 2,
                    background: 'linear-gradient(45deg, #ffffff 30%, #e0e0e0 90%)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    color: 'transparent',
                  }}
                >
                  Monitor Web
                  <Box
                    component="span"
                    sx={{
                      display: 'block',
                      background: 'linear-gradient(45deg, #ffd700 30%, #ff6b00 90%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      color: 'transparent',
                    }}
                  >
                    Content With FreshLense
                  </Box>
                </Typography>
                
                <Fade in={isVisible} timeout={1200}>
                  <Typography
                    variant="body1"
                    sx={{
                      mb: 3,
                      opacity: 0.9,
                      lineHeight: 1.5,
                      fontSize: { xs: '1rem', md: '1.1rem' },
                      maxWidth: '90%',
                    }}
                  >
                    FreshLense automatically tracks website changes, verifies factual accuracy, 
                    and provides intelligent insights for technical documentation, blogs, and information sites.
                  </Typography>
                </Fade>

                <Fade in={isVisible} timeout={1600}>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {isAuthenticated ? (
                      <Button
                        component={Link}
                        to="/dashboard"
                        variant="contained"
                        size="medium"
                        endIcon={<ArrowForward />}
                        sx={{
                          bgcolor: 'white',
                          color: theme.palette.primary.main,
                          px: 3,
                          py: 1,
                          fontSize: '0.9rem',
                          fontWeight: 600,
                          borderRadius: 2,
                          '&:hover': {
                            bgcolor: 'grey.100',
                            transform: 'translateY(-2px)',
                            boxShadow: 4,
                          },
                          transition: 'all 0.3s ease',
                        }}
                      >
                        Go to Dashboard
                      </Button>
                    ) : (
                      <>
                        <Button
                          component={Link}
                          to="/register"
                          variant="contained"
                          size="medium"
                          endIcon={<RocketLaunch />}
                          sx={{
                            bgcolor: 'white',
                            color: theme.palette.primary.main,
                            px: 3,
                            py: 1,
                            fontSize: '0.9rem',
                            fontWeight: 600,
                            borderRadius: 2,
                            '&:hover': {
                              bgcolor: 'grey.100',
                              transform: 'translateY(-2px)',
                              boxShadow: 4,
                            },
                            transition: 'all 0.3s ease',
                          }}
                        >
                          Start Free Trial
                        </Button>
                        <Button
                          component={Link}
                          to="/login"
                          variant="outlined"
                          size="medium"
                          sx={{
                            borderColor: 'white',
                            color: 'white',
                            px: 3,
                            py: 1,
                            fontSize: '0.9rem',
                            fontWeight: 600,
                            borderRadius: 2,
                            '&:hover': {
                              bgcolor: 'white',
                              color: theme.palette.primary.main,
                              transform: 'translateY(-2px)',
                              boxShadow: 4,
                            },
                            transition: 'all 0.3s ease',
                          }}
                        >
                          Sign In
                        </Button>
                      </>
                    )}
                  </Box>
                </Fade>
              </Box>
            </Slide>

            <Slide in={isVisible} direction="left" timeout={800}>
              <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                <Box
                  sx={{
                    position: 'relative',
                    perspective: '1000px',
                    maxWidth: 450,
                    width: '100%',
                  }}
                >
                  {/* Main Dashboard Preview - Smaller */}
                  <Box
                    sx={{
                      background: `linear-gradient(145deg, ${alpha('#fff', 0.95)} 0%, ${alpha('#f8f9fa', 0.95)} 100%)`,
                      borderRadius: 3,
                      p: 3,
                      boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.5)',
                      transform: 'rotateY(5deg) rotateX(5deg)',
                      transition: 'transform 0.5s ease',
                      '&:hover': {
                        transform: 'rotateY(0deg) rotateX(0deg)',
                      },
                    }}
                  >
                    {/* Mock Dashboard Content */}
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box
                        sx={{
                          width: 32,
                          height: 32,
                          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                          borderRadius: 2,
                          mr: 2,
                        }}
                      />
                      <Typography variant="subtitle1" fontWeight="bold" color="text.primary">
                        FreshLense Dashboard
                      </Typography>
                    </Box>

                    {/* Mock Stats - Compact */}
                    <Box sx={{ display: 'flex', gap: 1.5, mb: 2.5 }}>
                      {[
                        { value: '24', label: 'Sites' },
                        { value: '156', label: 'Changes' },
                        { value: '98%', label: 'Accuracy' },
                      ].map((stat, index) => (
                        <Box
                          key={index}
                          sx={{
                            flex: 1,
                            textAlign: 'center',
                            p: 1.5,
                            background: alpha(theme.palette.primary.main, 0.1),
                            borderRadius: 2,
                          }}
                        >
                          <Typography variant="h6" fontWeight="bold" color="primary.main" sx={{ fontSize: '1rem' }}>
                            {stat.value}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                            {stat.label}
                          </Typography>
                        </Box>
                      ))}
                    </Box>

                    {/* Mock Activity - Compact */}
                    <Box>
                      {[
                        'React docs updated - 5 changes',
                        'Tech blog fact-checked - 3 claims',
                        'API docs monitored - No changes',
                      ].map((activity, index) => (
                        <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <CheckCircle sx={{ fontSize: 12, color: 'success.main', mr: 1 }} />
                          <Typography variant="caption" color="text.primary">
                            {activity}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Slide>
          </Box>
        </Container>
      </Box>

      {/* Stats Section - Compact */}
      <Box sx={{ py: 6, bgcolor: 'background.default' }}>
        <Container maxWidth="lg">
          <Fade in={isVisible} timeout={1000}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 3 }}>
              {stats.map((stat, index) => (
                <Box key={index} sx={{ textAlign: 'center', minWidth: 120 }}>
                  <Zoom in={isVisible} timeout={800 + index * 200}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 0.5 }}>
                      <Box
                        sx={{
                          color: theme.palette.primary.main,
                          mr: 0.5,
                        }}
                      >
                        {stat.icon}
                      </Box>
                      <Typography
                        variant="h4"
                        fontWeight="bold"
                        color="primary.main"
                        sx={{ fontSize: '2rem' }}
                      >
                        {stat.number}
                      </Typography>
                    </Box>
                  </Zoom>
                  <Typography variant="body2" color="text.secondary">
                    {stat.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Fade>
        </Container>
      </Box>

      {/* Features Section - Unchanged */}
      <Box sx={{ py: 8, bgcolor: 'background.paper' }}>
        <Container maxWidth="lg">
          <Fade in={isVisible} timeout={800}>
            <Box sx={{ textAlign: 'center', mb: 6 }}>
              <Typography
                variant="h3"
                component="h2"
                fontWeight="bold"
                sx={{ mb: 2, fontSize: { xs: '2rem', md: '2.5rem' } }}
              >
                Powerful Features
              </Typography>
              <Typography
                variant="body1"
                color="text.secondary"
                sx={{ maxWidth: 600, mx: 'auto' }}
              >
                Everything you need to ensure your web content remains accurate and up-to-date
              </Typography>
            </Box>
          </Fade>

          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, justifyContent: 'center' }}>
            {features.map((feature, index) => (
              <Box key={index} sx={{ width: { xs: '100%', sm: 'calc(50% - 12px)', md: 'calc(33.333% - 16px)' }, minWidth: 280 }}>
                <Slide in={isVisible} direction="up" timeout={800 + index * 200}>
                  <Card
                    sx={{
                      height: '100%',
                      border: 'none',
                      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                      borderRadius: 3,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
                      },
                    }}
                  >
                    <CardContent sx={{ p: 3, textAlign: 'center' }}>
                      <Box
                        sx={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 70,
                          height: 70,
                          borderRadius: '50%',
                          background: `linear-gradient(45deg, ${feature.color}, ${alpha(feature.color, 0.7)})`,
                          color: 'white',
                          mb: 2,
                        }}
                      >
                        {feature.icon}
                      </Box>
                      <Typography
                        variant="h5"
                        component="h3"
                        fontWeight="bold"
                        sx={{ mb: 1, fontSize: '1.25rem' }}
                      >
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Slide>
              </Box>
            ))}
          </Box>
        </Container>
      </Box>

      {/* CTA Section - Compact */}
      <Box
        sx={{
          py: 8,
          background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.secondary.dark} 100%)`,
          color: 'white',
        }}
      >
        <Container maxWidth="md">
          <Fade in={isVisible} timeout={1000}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography
                variant="h4"
                component="h2"
                fontWeight="bold"
                sx={{ mb: 2, fontSize: { xs: '1.75rem', md: '2rem' } }}
              >
                Ready to Ensure Content Accuracy?
              </Typography>
              <Typography
                variant="body1"
                sx={{ mb: 3, opacity: 0.9 }}
              >
                Join developers, technical writers, and content managers who trust FreshLense 
                to maintain their content integrity.
              </Typography>
              {isAuthenticated ? (
                <Button
                  component={Link}
                  to="/dashboard"
                  variant="contained"
                  size="medium"
                  endIcon={<ArrowForward />}
                  sx={{
                    bgcolor: 'white',
                    color: theme.palette.primary.main,
                    px: 4,
                    py: 1,
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: 2,
                    '&:hover': {
                      bgcolor: 'grey.100',
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  Go to Dashboard
                </Button>
              ) : (
                <Button
                  component={Link}
                  to="/register"
                  variant="contained"
                  size="medium"
                  endIcon={<RocketLaunch />}
                  sx={{
                    bgcolor: 'white',
                    color: theme.palette.primary.main,
                    px: 4,
                    py: 1,
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: 2,
                    '&:hover': {
                      bgcolor: 'grey.100',
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                    transition: 'all 0.3s ease',
                  }}
                >
                  Start Your Free Trial
                </Button>
              )}
            </Box>
          </Fade>
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 4, bgcolor: 'background.default', borderTop: `1px solid ${theme.palette.divider}` }}>
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  borderRadius: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '0.8rem',
                }}
              >
                FL
              </Box>
              <Typography variant="body2" color="text.primary" fontWeight="500">
                FreshLense
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              © 2024 FreshLense. All rights reserved.
            </Typography>
          </Box>
        </Container>
      </Box>

      {/* Add CSS animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(180deg); }
        }
      `}</style>
    </Box>
  );
};

export default LandingPage;