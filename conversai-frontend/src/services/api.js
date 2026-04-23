const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generate an explanation from text using the ConversAI backend.
 * 
 * @param {Object} data - Request data
 * @param {string} data.text - Text to explain (100-5000 chars)
 * @param {string} data.duration - Duration preference ('short' | 'medium')
 * @param {string} [data.instruction] - Optional custom instruction
 * @param {boolean} [data.avatarEnabled=true] - Whether to include avatar
 * @returns {Promise<Object>} Aggregated multimodal response
 */
export async function generateExplanation(data) {
  const response = await fetch(`${API_URL}/api/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: data.text,
      duration: data.duration || 'medium',
      instruction: data.instruction || null,
      avatarEnabled: data.avatarEnabled ?? true,
    }),
  });

  if (!response.ok) {
    let errorMessage = 'Something went wrong. Please try again.';
    
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (errorData.detail?.message) {
        errorMessage = errorData.detail.message;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // If parsing fails, use status-based message
      if (response.status === 400) {
        errorMessage = 'Invalid input. Please check your text and try again.';
      } else if (response.status === 500) {
        errorMessage = 'Server error. Our team has been notified.';
      } else if (response.status === 503) {
        errorMessage = 'Service temporarily unavailable. Please try again later.';
      }
    }
    
    const error = new Error(errorMessage);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

/**
 * Check if the backend API is healthy.
 * @returns {Promise<boolean>}
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Generate a follow-up explanation based on previous context + question.
 * 
 * @param {Object} data - Request data
 * @param {string} data.originalText - Original text that was explained
 * @param {string} data.followUpQuestion - Follow-up question from user
 * @param {string} [data.duration='short'] - Duration preference
 * @param {boolean} [data.avatarEnabled=true] - Whether to include avatar
 * @returns {Promise<Object>} Aggregated multimodal response
 */
export async function generateFollowUp(data) {
  const response = await fetch(`${API_URL}/api/explain/followup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      originalText: data.originalText,
      followUpQuestion: data.followUpQuestion,
      duration: data.duration || 'short',
      avatarEnabled: data.avatarEnabled ?? true,
    }),
  });

  if (!response.ok) {
    let errorMessage = 'Follow-up failed. Please try again.';
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (errorData.detail?.message) {
        errorMessage = errorData.detail.message;
      }
    } catch {
      // Use default message
    }
    const error = new Error(errorMessage);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export default {
  generateExplanation,
  generateFollowUp,
  checkHealth,
};
