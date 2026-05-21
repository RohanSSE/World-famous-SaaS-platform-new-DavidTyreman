import type { FormEvent } from 'react';

import { useState, useCallback } from 'react';

import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import InputAdornment from '@mui/material/InputAdornment';

import { useRouter } from 'src/routes/hooks';

import { Iconify } from 'src/components/iconify';

import { saveAuthSession } from 'src/auth/session';

// ----------------------------------------------------------------------

export function SignInView() {
  const router = useRouter();

  const [mode, setMode] = useState<'sign-in' | 'sign-up'>('sign-in');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const isSignUp = mode === 'sign-up';

  const handleModeChange = useCallback(
    (nextMode: 'sign-in' | 'sign-up') => {
      setMode(nextMode);
      setErrorMessage(null);
    },
    []
  );

  const handleAuthSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      const trimmedEmail = email.trim().toLowerCase();
      const trimmedName = fullName.trim();

      if (!trimmedEmail || !password) {
        setErrorMessage('Email and password are required.');
        return;
      }

      if (isSignUp && !trimmedName) {
        setErrorMessage('Full name is required for sign up.');
        return;
      }

      if (isSignUp && password !== confirmPassword) {
        setErrorMessage('Passwords do not match.');
        return;
      }

      saveAuthSession({
        email: trimmedEmail,
        name: trimmedName || 'Admin User',
        mode,
        loggedInAt: new Date().toISOString(),
      });

      router.replace('/');
    },
    [confirmPassword, email, fullName, isSignUp, mode, password, router]
  );

  const renderForm = (
    <Box
      component="form"
      onSubmit={handleAuthSubmit}
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        flexDirection: 'column',
      }}
    >
      {isSignUp && (
        <TextField
          fullWidth
          name="fullName"
          label="Full name"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          sx={{ mb: 3 }}
          slotProps={{
            inputLabel: { shrink: true },
          }}
        />
      )}

      <TextField
        fullWidth
        name="email"
        label="Email address"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        sx={{ mb: 3 }}
        slotProps={{
          inputLabel: { shrink: true },
        }}
      />

      {!isSignUp && (
        <Link variant="body2" color="inherit" sx={{ mb: 1.5 }}>
          Forgot password?
        </Link>
      )}

      <TextField
        fullWidth
        name="password"
        label="Password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        type={showPassword ? 'text' : 'password'}
        slotProps={{
          inputLabel: { shrink: true },
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                  <Iconify icon={showPassword ? 'solar:eye-bold' : 'solar:eye-closed-bold'} />
                </IconButton>
              </InputAdornment>
            ),
          },
        }}
        sx={{ mb: 3 }}
      />

      {isSignUp && (
        <TextField
          fullWidth
          name="confirmPassword"
          label="Confirm password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          type={showPassword ? 'text' : 'password'}
          slotProps={{
            inputLabel: { shrink: true },
          }}
          sx={{ mb: 3 }}
        />
      )}

      {errorMessage && (
        <Alert severity="error" sx={{ mb: 3, width: 1 }}>
          {errorMessage}
        </Alert>
      )}

      <Button
        fullWidth
        size="large"
        type="submit"
        color="inherit"
        variant="contained"
      >
        {isSignUp ? 'Create account' : 'Sign in'}
      </Button>
    </Box>
  );

  return (
    <>
      <Box
        sx={{
          gap: 1.5,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          mb: 5,
        }}
      >
        <Typography variant="h5">{isSignUp ? 'Sign up' : 'Sign in'}</Typography>
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
          }}
        >
          {isSignUp ? 'Already have an account?' : 'Don’t have an account?'}
          <Link
            component="button"
            type="button"
            variant="subtitle2"
            sx={{ ml: 0.5 }}
            onClick={() => handleModeChange(isSignUp ? 'sign-in' : 'sign-up')}
          >
            {isSignUp ? 'Sign in' : 'Get started'}
          </Link>
        </Typography>
      </Box>
      {renderForm}
      <Divider sx={{ my: 3, '&::before, &::after': { borderTopStyle: 'dashed' } }}>
        <Typography
          variant="overline"
          sx={{ color: 'text.secondary', fontWeight: 'fontWeightMedium' }}
        >
          OR
        </Typography>
      </Divider>
      <Box
        sx={{
          gap: 1,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <IconButton color="inherit">
          <Iconify width={22} icon="socials:google" />
        </IconButton>
        <IconButton color="inherit">
          <Iconify width={22} icon="socials:github" />
        </IconButton>
        <IconButton color="inherit">
          <Iconify width={22} icon="socials:twitter" />
        </IconButton>
      </Box>
    </>
  );
}
