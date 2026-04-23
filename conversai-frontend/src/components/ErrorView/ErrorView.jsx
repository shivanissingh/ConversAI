import { motion } from 'framer-motion';
import './ErrorView.css';

/**
 * ErrorView Component
 * User-friendly error display with retry option.
 */
function ErrorView({ error, onRetry, onBack }) {
    const getErrorInfo = (error) => {
        const message = error?.message || error || 'Something went wrong';

        // Categorize error for icon/styling
        if (message.includes('network') || message.includes('fetch')) {
            return {
                icon: '🌐',
                title: 'Connection Error',
                message: 'Unable to reach the server. Please check your internet connection.',
                canRetry: true,
            };
        }

        if (message.includes('timeout')) {
            return {
                icon: '⏱️',
                title: 'Request Timeout',
                message: 'The request took too long. Please try again.',
                canRetry: true,
            };
        }

        if (message.includes('validation') || message.includes('Invalid')) {
            return {
                icon: '📝',
                title: 'Invalid Input',
                message,
                canRetry: false,
            };
        }

        if (message.includes('Server error')) {
            return {
                icon: '🔧',
                title: 'Server Error',
                message: 'Our servers are having issues. Our team has been notified.',
                canRetry: true,
            };
        }

        return {
            icon: '⚠️',
            title: 'Oops!',
            message,
            canRetry: true,
        };
    };

    const errorInfo = getErrorInfo(error);

    return (
        <motion.div
            className="error-view"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <motion.div
                className="error-view__card"
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ delay: 0.1 }}
            >
                <motion.div
                    className="error-view__icon"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                >
                    {errorInfo.icon}
                </motion.div>

                <h2 className="error-view__title">{errorInfo.title}</h2>

                <p className="error-view__message">{errorInfo.message}</p>

                <div className="error-view__actions">
                    {errorInfo.canRetry && (
                        <motion.button
                            className="error-view__button error-view__button--primary"
                            onClick={onRetry}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            Try Again
                        </motion.button>
                    )}

                    <motion.button
                        className="error-view__button error-view__button--secondary"
                        onClick={onBack}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        Start Over
                    </motion.button>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default ErrorView;
