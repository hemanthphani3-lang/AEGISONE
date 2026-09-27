import { env } from '@/app/config/env';
import { keycloakService } from '@/services/auth/keycloakService';
import { ApiError } from '@/types/api';
import { generateCorrelationId } from '@/utils/correlation';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = env.apiBaseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private getHeaders(customHeaders?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Correlation-ID': generateCorrelationId(),
      ...customHeaders,
    };

    const token = keycloakService.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response, correlationId?: string): Promise<T> {
    if (response.ok) {
      if (response.status === 240 || response.status === 204) {
        return {} as T;
      }
      return response.json();
    }

    let errorDetail: any = null;
    try {
      errorDetail = await response.json();
    } catch {
      errorDetail = await response.text();
    }

    const message =
      typeof errorDetail === 'object' && errorDetail?.detail
        ? typeof errorDetail.detail === 'string'
          ? errorDetail.detail
          : JSON.stringify(errorDetail.detail)
        : `Request failed with status ${response.status}`;

    const serverCorrelationId = response.headers.get('X-Correlation-ID');
    const apiError: ApiError = {
      status: response.status,
      message,
      detail: errorDetail,
      correlationId: serverCorrelationId || correlationId || undefined,
    };

    if (response.status === 401) {
      console.warn('Unauthorized access detected (401). Session may be expired.');
    } else if (response.status === 403) {
      console.warn('Forbidden resource requested (403). User lacks permission.');
    }

    throw apiError;
  }

  public async get<T>(path: string, headers?: Record<string, string>): Promise<T> {
    const correlationId = generateCorrelationId();
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'GET',
        headers: this.getHeaders({ 'X-Correlation-ID': correlationId, ...headers }),
      });
      return await this.handleResponse<T>(response, correlationId);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        status: 0,
        message: 'Network connection failed. Backend service is unavailable.',
        correlationId,
      } as ApiError;
    }
  }

  public async post<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    const correlationId = generateCorrelationId();
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: this.getHeaders({ 'X-Correlation-ID': correlationId, ...headers }),
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
      return await this.handleResponse<T>(response, correlationId);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        status: 0,
        message: 'Network connection failed. Backend service is unavailable.',
        correlationId,
      } as ApiError;
    }
  }

  public async patch<T>(path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    const correlationId = generateCorrelationId();
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'PATCH',
        headers: this.getHeaders({ 'X-Correlation-ID': correlationId, ...headers }),
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
      return await this.handleResponse<T>(response, correlationId);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        status: 0,
        message: 'Network connection failed. Backend service is unavailable.',
        correlationId,
      } as ApiError;
    }
  }

  public async delete<T>(path: string, headers?: Record<string, string>): Promise<T> {
    const correlationId = generateCorrelationId();
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'DELETE',
        headers: this.getHeaders({ 'X-Correlation-ID': correlationId, ...headers }),
      });
      return await this.handleResponse<T>(response, correlationId);
    } catch (err: any) {
      if (err.status) throw err;
      throw {
        status: 0,
        message: 'Network connection failed. Backend service is unavailable.',
        correlationId,
      } as ApiError;
    }
  }
}

export const apiClient = new ApiClient();
