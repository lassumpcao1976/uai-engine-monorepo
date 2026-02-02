import axios, { AxiosInstance } from 'axios'

export interface UAIEngineConfig {
  apiUrl: string
  token?: string
}

export class UAIEngine {
  private client: AxiosInstance

  constructor(config: UAIEngineConfig) {
    this.client = axios.create({
      baseURL: `${config.apiUrl}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (config.token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${config.token}`
    }
  }

  setToken(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  async register(email: string, password: string, fullName?: string) {
    const response = await this.client.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    })
    return response.data
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', {
      email,
      password,
    })
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  async createProject(name: string, description?: string) {
    const response = await this.client.post('/projects', {
      name,
      description,
    })
    return response.data
  }

  async listProjects() {
    const response = await this.client.get('/projects')
    return response.data
  }

  async getProject(projectId: number) {
    const response = await this.client.get(`/projects/${projectId}`)
    return response.data
  }

  async createVersion(projectId: number, prompt: string) {
    const response = await this.client.post(`/versions/projects/${projectId}/versions`, {
      prompt,
    })
    return response.data
  }

  async createBuild(versionId: number) {
    const response = await this.client.post(`/builds/versions/${versionId}/builds`)
    return response.data
  }

  async getBuild(buildId: number) {
    const response = await this.client.get(`/builds/${buildId}`)
    return response.data
  }

  async getCredits() {
    const response = await this.client.get('/credits/balance')
    return response.data
  }
}

export default UAIEngine
