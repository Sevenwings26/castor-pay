import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from './store/store';
import { setActiveModal } from './store/slices/uiSlice';
import { LoginPage } from './pages/auth/LoginPage';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ToastContainer } from './components/common/ToastContainer';
import { DashboardPage } from './pages/merchant/DashboardPage';
import { TransactionsPage } from './pages/merchant/TransactionsPage';
import { VirtualAccountsPage } from './pages/merchant/VirtualAccountsPage';
import { FXExchangePage } from './pages/merchant/FXExchangePage';
import { EscrowPage } from './pages/merchant/EscrowPage';
import { DeveloperPage } from './pages/merchant/DeveloperPage';
import { TreasuryPage } from './pages/admin/TreasuryPage';
import { DLQMonitorPage } from './pages/admin/DLQMonitorPage';
import { ReconciliationPage } from './pages/admin/ReconciliationPage';
import { InitializePaymentModal } from './components/payments/InitializePaymentModal';
import { CreateVirtualAccountModal } from './components/virtualAccounts/CreateVirtualAccountModal';
import { SimulateDepositModal } from './components/virtualAccounts/SimulateDepositModal';

export const App: React.FC = () => {
  const dispatch = useDispatch();
  const { token, activePortal } = useSelector((state: RootState) => state.auth);
  const activeModal = useSelector((state: RootState) => state.ui.activeModal);

  const [currentTab, setCurrentTab] = useState<string>(
    activePortal === 'ADMIN' ? 'admin-treasury' : 'overview'
  );

  // Keep tab aligned when portal changes
  useEffect(() => {
    if (activePortal === 'ADMIN' && !currentTab.startsWith('admin-')) {
      setCurrentTab('admin-treasury');
    } else if (activePortal === 'MERCHANT' && currentTab.startsWith('admin-')) {
      setCurrentTab('overview');
    }
  }, [activePortal, currentTab]);

  if (!token) {
    return (
      <>
        <LoginPage />
        <ToastContainer />
      </>
    );
  }

  const renderActivePage = () => {
    switch (currentTab) {
      // Merchant Views
      case 'overview':
        return <DashboardPage onNavigate={setCurrentTab} />;
      case 'transactions':
        return <TransactionsPage />;
      case 'virtual-accounts':
        return <VirtualAccountsPage />;
      case 'fx':
        return <FXExchangePage />;
      case 'escrow':
        return <EscrowPage />;
      case 'developer':
        return <DeveloperPage />;

      // Admin Views
      case 'admin-treasury':
        return <TreasuryPage />;
      case 'admin-dlq':
        return <DLQMonitorPage />;
      case 'admin-recon':
        return <ReconciliationPage />;

      default:
        return <DashboardPage onNavigate={setCurrentTab} />;
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar Navigation */}
      <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto animate-in fade-in duration-150">
          {renderActivePage()}
        </main>
      </div>

      {/* Global Modals */}
      <InitializePaymentModal
        isOpen={activeModal === 'NEW_PAYMENT'}
        onClose={() => dispatch(setActiveModal(null))}
      />
      <CreateVirtualAccountModal
        isOpen={activeModal === 'CREATE_VA'}
        onClose={() => dispatch(setActiveModal(null))}
      />
      <SimulateDepositModal
        isOpen={activeModal === 'SIMULATE_DEPOSIT'}
        onClose={() => dispatch(setActiveModal(null))}
      />

      {/* Reactive Toast Notification System */}
      <ToastContainer />
    </div>
  );
};

export default App;
