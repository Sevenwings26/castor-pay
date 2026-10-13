import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Zap, ShieldCheck, UserCheck, ArrowRight } from 'lucide-react';
import { useLoginMutation, useRegisterMutation } from '../../api/apiSlice';
import { setCredentials } from '../../store/slices/authSlice';
import { addToast } from '../../store/slices/uiSlice';
import { Button } from '../../components/common/Button';

export const LoginPage: React.FC = () => {
  const dispatch = useDispatch();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('demo@castorpay.dev');
  const [password, setPassword] = useState('CastorSecret123!');
  const [fullName, setFullName] = useState('Alex Oladipo');
  const [merchantName, setMerchantName] = useState('Demo Gaming Platform');

  const [login, { isLoading: isLoginLoading }] = useLoginMutation();
  const [register, { isLoading: isRegisterLoading }] = useRegisterMutation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mode === 'login') {
        const res = await login({ email, password }).unwrap();
        dispatch(
          setCredentials({
            token: res.access_token,
            email: res.email,
            role: res.role,
            merchantId: res.merchant_id,
          })
        );
        dispatch(
          addToast({
            type: 'success',
            title: 'Welcome to CastorPay',
            message: `Signed in as ${res.email} (${res.role}).`,
          })
        );
      } else {
        const res = await register({
          email,
          password,
          full_name: fullName,
          merchant_name: merchantName,
        }).unwrap();
        dispatch(
          setCredentials({
            token: res.access_token,
            email: res.email,
            role: res.role,
            merchantId: res.merchant_id,
          })
        );
        dispatch(
          addToast({
            type: 'success',
            title: 'Account Registered',
            message: `Created merchant business account for ${res.email}.`,
          })
        );
      }
    } catch (err: any) {
      dispatch(
        addToast({
          type: 'error',
          title: mode === 'login' ? 'Authentication Failed' : 'Registration Failed',
          message: err?.data?.detail || 'Invalid credentials or connection error.',
        })
      );
    }
  };

  const fillMerchantDemo = () => {
    setEmail('demo@castorpay.dev');
    setPassword('CastorSecret123!');
    setMode('login');
  };

  const fillAdminDemo = () => {
    setEmail('admin@castorpay.dev');
    setPassword('AdminSecret123!');
    setMode('login');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 selection:bg-brand-500 selection:text-white">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-600 text-white shadow-xl shadow-brand-900/40 mb-3">
            <Zap className="w-8 h-8 fill-white" />
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Castor<span className="text-brand-400">Pay</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">
            Embedded Finance & Payment Gateway
          </p>
        </div>

        {/* Card Container */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
          {/* Mode Tabs */}
          <div className="grid grid-cols-2 gap-1 bg-slate-950 p-1 rounded-xl mb-6 border border-slate-800">
            <button
              type="button"
              onClick={() => setMode('login')}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'login'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode('register')}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                mode === 'register'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Register Merchant
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Alex Oladipo"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Business / Platform Name
                  </label>
                  <input
                    type="text"
                    value={merchantName}
                    onChange={(e) => setMerchantName(e.target.value)}
                    required
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    placeholder="Gaming Micropayments Ltd"
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Account Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
                placeholder="name@business.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="••••••••••••"
              />
            </div>

            <Button
              type="submit"
              size="md"
              isLoading={isLoginLoading || isRegisterLoading}
              icon={<ArrowRight className="w-4 h-4" />}
              className="w-full mt-2"
            >
              {mode === 'login' ? 'Sign In to Gateway' : 'Create Merchant Account'}
            </Button>
          </form>

          {/* Demo Sandbox Quick Fill */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2.5 text-center">
              1-Click Demo Credentials
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={fillMerchantDemo}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-left transition-colors"
              >
                <div className="text-xs font-bold text-brand-400 flex items-center gap-1">
                  <UserCheck className="w-3.5 h-3.5" /> Merchant Admin
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">demo@castorpay.dev</div>
              </button>

              <button
                type="button"
                onClick={fillAdminDemo}
                className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-left transition-colors"
              >
                <div className="text-xs font-bold text-purple-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Platform Admin
                </div>
                <div className="text-[10px] text-slate-400 truncate mt-0.5">admin@castorpay.dev</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
