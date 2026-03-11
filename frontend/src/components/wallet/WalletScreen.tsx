'use client';

import React, { useState } from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import FundWalletModal from './FundWalletModal';
import BankTransferModal from './BankTransferModal';
import { UITransaction } from '@/lib/utils';

interface WalletScreenProps {
  balance: number;
  transactions: UITransaction[];
  onFund: (amount: number) => void;
  onBankTransfer: (amount: number) => void;
}

export default function WalletScreen({ balance, transactions, onFund, onBankTransfer }: WalletScreenProps) {
  const [showAllTransactions, setShowAllTransactions] = useState(false);
  const [filterType, setFilterType] = useState('all'); // 'all', 'credit', 'debit'
  const [showFundModal, setShowFundModal] = useState(false);
  const [showBankModal, setShowBankModal] = useState(false);
  const [transferAmount, setTransferAmount] = useState(0);

  // Filter transactions
  const filteredTransactions = transactions ? (filterType === 'all'
    ? transactions
    : transactions.filter(txn => txn.type === filterType)) : [];

  // Show only recent 5 or all based on state
  const displayedTransactions = showAllTransactions
    ? filteredTransactions
    : filteredTransactions.slice(0, 5);

  const handleInitiateFund = (amount: number) => {
    onFund(amount);
    setShowFundModal(false);
  };

  const handleInitiateBankTransfer = (amount: number) => {
    setTransferAmount(amount);
    setShowFundModal(false);
    setShowBankModal(true);
  };

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Balance Card */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy}, #0f1b33)`, borderRadius: 16, padding: "28px 32px",
        marginBottom: 24, position: "relative", overflow: "hidden",
        boxShadow: "0 12px 32px rgba(27,42,74,0.25)"
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, borderRadius: "50%", background: "rgba(232,168,56,0.06)" }} />
        <div style={{ position: "absolute", bottom: -60, right: 80, width: 160, height: 160, borderRadius: "50%", background: "rgba(232,168,56,0.04)" }} />

        <div style={{ position: "relative" }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", fontWeight: 500, letterSpacing: "0.5px" }}>AVAILABLE BALANCE</div>
          <div style={{ fontSize: 38, fontWeight: 800, color: "#fff", marginTop: 8, fontFamily: "'Space Mono', monospace" }}>₦{balance.toLocaleString()}</div>
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            <button onClick={() => setShowFundModal(true)} style={{
              padding: "10px 24px", borderRadius: 10, border: "none", cursor: "pointer",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
              fontWeight: 700, fontSize: 14, fontFamily: "inherit"
            }}>+ Fund Wallet</button>
            <button onClick={() => setShowAllTransactions(true)} style={{
              padding: "10px 24px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)",
              cursor: "pointer", background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.7)",
              fontWeight: 600, fontSize: 14, fontFamily: "inherit"
            }}>Transaction History</button>
          </div>
        </div>
      </div>

      {/* Funding Methods */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Card", desc: "Visa / MC", emoji: "💳" },
          { label: "Transfer", desc: "Bank", emoji: "🏦" },
          { label: "USSD", desc: "*737#", emoji: "📱" },
          { label: "LibertyPay", desc: "Zero fee", emoji: "⚡" },
        ].map((m, i) => (
          <button key={i} onClick={() => setShowFundModal(true)} style={{
            background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px 12px",
            cursor: "pointer", textAlign: "center", fontFamily: "inherit"
          }}>
            <div style={{ fontSize: 24, marginBottom: 6 }}>{m.emoji}</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{m.label}</div>
            <div style={{ fontSize: 11, color: S.grayLight }}>{m.desc}</div>
          </button>
        ))}
      </div>

      {/* Transactions */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        {/* Header with filters */}
        <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>
              {showAllTransactions ? 'Transaction History' : 'Recent Transactions'}
            </h3>
            <button
              onClick={() => setShowAllTransactions(!showAllTransactions)}
              style={{
                background: "transparent",
                border: "none",
                color: S.gold,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "inherit"
              }}
            >
              {showAllTransactions ? '← Back' : 'View All →'}
            </button>
          </div>

          {/* Filter buttons */}
          {showAllTransactions && (
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { value: 'all', label: 'All', icon: '📊' },
                { value: 'credit', label: 'Credits', icon: '💰' },
                { value: 'debit', label: 'Debits', icon: '💸' }
              ].map(filter => (
                <button
                  key={filter.value}
                  onClick={() => setFilterType(filter.value)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 8,
                    border: filterType === filter.value ? `2px solid ${S.gold}` : "1px solid #e2e8f0",
                    background: filterType === filter.value ? S.goldPale : "#fff",
                    color: filterType === filter.value ? S.gold : S.gray,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    fontFamily: "inherit",
                    transition: "all 0.2s"
                  }}
                >
                  {filter.icon} {filter.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Transaction list */}
        {displayedTransactions.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: S.grayLight }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>No transactions found</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>Your transaction history will appear here</div>
          </div>
        ) : (
          <>
            {displayedTransactions.map((txn, i) => (
              <div key={txn.id} style={{
                padding: "14px 20px", display: "flex", alignItems: "center", gap: 14,
                borderBottom: i < displayedTransactions.length - 1 ? "1px solid #f8fafc" : "none",
                transition: "background 0.2s",
                cursor: "pointer"
              }}
                onMouseEnter={(e) => e.currentTarget.style.background = "#f8fafc"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <div style={{
                  width: 38, height: 38, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
                  background: txn.type === "credit" ? S.greenBg : S.redBg,
                  color: txn.type === "credit" ? S.green : S.red
                }}>
                  {txn.type === "credit" ? Icons.arrowDown : Icons.arrowUp}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{txn.description}</div>
                  <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2 }}>
                    {txn.date} • {txn.ref}
                    {txn.status && txn.status !== 'completed' && (
                      <span style={{
                        marginLeft: 8,
                        padding: "2px 6px",
                        borderRadius: 4,
                        fontSize: 10,
                        fontWeight: 700,
                        background: txn.status === 'pending' ? S.goldPale : S.redBg,
                        color: txn.status === 'pending' ? S.gold : S.red
                      }}>
                        {txn.status.toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{
                    fontSize: 15, fontWeight: 700, fontFamily: "'Space Mono', monospace",
                    color: txn.type === "credit" ? S.green : S.red
                  }}>
                    {txn.type === "credit" ? "+" : "−"}₦{txn.amount.toLocaleString()}
                  </div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>Bal: ₦{txn.balance.toLocaleString()}</div>
                </div>
              </div>
            ))}

            {/* Show count when viewing all */}
            {showAllTransactions && (
              <div style={{
                padding: "12px 20px",
                background: "#f8fafc",
                textAlign: "center",
                fontSize: 12,
                color: S.gray,
                fontWeight: 600
              }}>
                Showing {displayedTransactions.length} of {filteredTransactions.length} transactions
              </div>
            )}
          </>
        )}
      </div>

      {/* Modals */}
      {showFundModal && (
        <FundWalletModal
          onClose={() => setShowFundModal(false)}
          onFund={handleInitiateFund}
          onBankTransfer={handleInitiateBankTransfer}
        />
      )}
      {showBankModal && (
        <BankTransferModal
          amount={transferAmount}
          onClose={() => setShowBankModal(false)}
          onSuccess={() => {
            onBankTransfer(transferAmount); // Or handle success refreshes here
            setShowBankModal(false);
          }}
        />
      )}
    </div>
  );
}
