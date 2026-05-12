/**
 * API Client v2 - Frontend API Layer
 * 
 * Communicates with backend orchestration service.
 * Handles all workflow phases: input → clarification → spec → preflight → execution → validation
 */

import { TASK_LABELS } from './constants';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001/api/v2';
const REQUEST_TIMEOUT_MS = Number(process.env.REACT_APP_API_TIMEOUT_MS || 15000);

class APIClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.timeoutMs = REQUEST_TIMEOUT_MS;
  }

  async request(path, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseURL}${path}`, {
        ...options,
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorMessage = `Request failed: ${response.status} ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {}
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`请求超时（>${this.timeoutMs}ms），请确认后端服务已启动且 ${this.baseURL} 可访问`);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // SESSION MANAGEMENT
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Create a new task session
   * 
   * Supports both:
   * - Full label objects: { id, type, value, label }
   * - String IDs: resolved via TASK_LABELS by id
   */
  async createSession(userText, selectedLabels = []) {
    const normalizedLabels = selectedLabels
      .map((label) => {
        if (typeof label === 'string') {
          return TASK_LABELS.find((item) => item.id === label) || null;
        }
        if (label && typeof label === 'object') {
          return label;
        }
        return null;
      })
      .filter(Boolean);

    const selectedDomains = normalizedLabels
      .filter((label) => label.type === 'domain')
      .map((label) => label.value);

    const selectedCharacteristics = normalizedLabels
      .flatMap((label) => {
        if (label.type === 'characteristic') {
          return [label.value];
        }
        return Array.isArray(label.characteristics) ? label.characteristics : [];
      })
      .filter(Boolean);

    return this.request('/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: userText,
        selected_domains: [...new Set(selectedDomains)],
        selected_characteristics: [...new Set(selectedCharacteristics)],
      }),
    });
  }

  /**
   * Get session state
   */
  async getSession(sessionId) {
    return this.request(`/sessions/${sessionId}`);
  }

  /**
   * List all sessions
   */
  async listSessions() {
    return this.request('/sessions');
  }

  /**
   * Delete a session by ID
   */
  async deleteSession(sessionId) {
    return this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // ════════════════════════════════════════════════════════════════════════
  // CLARIFICATION PHASE
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Process clarification - get schema or skip
   */
  async processClarification(sessionId) {
    return this.request(`/sessions/${sessionId}/clarification`, { method: 'POST' });
  }

  /**
   * Submit clarification answers
   */
  async submitClarificationAnswers(sessionId, answers) {
    return this.request(`/sessions/${sessionId}/clarification/answers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers }),
    });
  }

  // ════════════════════════════════════════════════════════════════════════
  // SPECIFICATION PHASE
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Align specification
   */
  async alignSpecification(sessionId) {
    return this.request(`/sessions/${sessionId}/specification`, { method: 'POST' });
  }

  /**
   * Update specification
   */
  async updateSpecification(sessionId, updates) {
    return this.request(`/sessions/${sessionId}/specification`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
  }

  // ════════════════════════════════════════════════════════════════════════
  // PREFLIGHT PHASE
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Run preflight validation
   */
  async runPreflight(sessionId) {
    return this.request(`/sessions/${sessionId}/preflight`, { method: 'POST' });
  }

  // ════════════════════════════════════════════════════════════════════════
  // EXECUTION PHASE
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Execute task
   */
  async execute(sessionId) {
    return this.request(`/sessions/${sessionId}/execute`, { method: 'POST' });
  }

  // ════════════════════════════════════════════════════════════════════════
  // VALIDATION PHASE
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Validate output
   */
  async validateOutput(sessionId) {
    return this.request(`/sessions/${sessionId}/validate`, { method: 'POST' });
  }

  // ════════════════════════════════════════════════════════════════════════
  // ERROR HANDLING
  // ════════════════════════════════════════════════════════════════════════

  /**
   * Handle API errors
   */
  static handleError(error) {
    console.error('API Error:', error);
    return {
      success: false,
      error: error.message || 'Unknown error occurred',
    };
  }
}

export default new APIClient();
