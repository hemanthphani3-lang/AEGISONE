import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { ShieldCheck, Mail, AlertCircle, CheckCircle2 } from 'lucide-react';
import { authApi } from '@/services/api/authApi';

interface MfaModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMfaSuccess: (newToken?: string) => void;
  userEmail?: string;
}

export const MfaModal: React.FC<MfaModalProps> = ({ isOpen, onClose, onMfaSuccess, userEmail }) => {
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    let timer: any;
    if (cooldown > 0) {
      timer = setInterval(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  if (!isOpen) return null;

  const handleSendOtp = async () => {
    setSendingOtp(true);
    setError(null);
    setMessage(null);
    try {
      const res = await authApi.sendMfaOtp(userEmail);
      setMessage(res.message);
      setCooldown(res.cooldown_seconds || 60);
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP code.');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      setError('Please enter a valid 6-digit OTP code.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.verifyMfaOtp(otpCode);
      onMfaSuccess(res.access_token);
      onClose();
    } catch (err: any) {
      setError(err.message || 'OTP verification failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-slate-200 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 p-6 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-white/10 rounded-xl backdrop-blur-md">
              <ShieldCheck className="w-6 h-6 text-indigo-200" />
            </div>
            <div>
              <h3 className="font-bold text-lg leading-tight">Multi-Factor Authentication</h3>
              <p className="text-xs text-indigo-200 mt-0.5">Email OTP Security Challenge</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{message}</span>
            </div>
          )}

          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700">Enter 6-Digit OTP Code</label>
                <button
                  type="button"
                  onClick={handleSendOtp}
                  disabled={sendingOtp || cooldown > 0}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 disabled:opacity-50 flex items-center gap-1"
                >
                  <Mail className="w-3.5 h-3.5" />
                  {sendingOtp
                    ? 'Sending...'
                    : cooldown > 0
                    ? `Resend in ${cooldown}s`
                    : 'Send / Resend OTP'}
                </button>
              </div>

              <input
                type="text"
                maxLength={6}
                placeholder="123456"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                className="w-full text-center text-2xl font-mono tracking-widest p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" size="md" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="md" loading={loading} disabled={loading || otpCode.length !== 6}>
                Verify MFA Code
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
