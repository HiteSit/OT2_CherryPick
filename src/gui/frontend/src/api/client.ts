import axios from 'axios'
import type {
  CsvListResponse,
  CsvUploadPayload,
  LabwareDocument,
  SettingsDocument,
  WorkflowRequest,
  WorkflowResponse,
} from './types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export interface PatchPayload {
  path: string
  value: unknown
}

export const fetchSettings = async (): Promise<SettingsDocument> => {
  const { data } = await api.get<SettingsDocument>('/settings')
  return data
}

export const patchSetting = async (payload: PatchPayload): Promise<SettingsDocument> => {
  const { data } = await api.patch<SettingsDocument>('/settings', payload)
  return data
}

export const replaceSettings = async (doc: Record<string, unknown>): Promise<SettingsDocument> => {
  const { data } = await api.put<SettingsDocument>('/settings', { data: doc })
  return data
}

export const fetchRawSettings = async (): Promise<string> => {
  const { data } = await api.get<string>('/settings/raw', { responseType: 'text' })
  return data
}

export const addWorkingPlateEntry = async (payload: {
  type: string
  labware_id?: string
  position_rack?: string
  connection?: string
}): Promise<SettingsDocument> => {
  const { data } = await api.post<SettingsDocument>('/settings/working-plate', payload)
  return data
}

export const deleteWorkingPlateEntry = async (index: number): Promise<SettingsDocument> => {
  const { data } = await api.delete<SettingsDocument>(`/settings/working-plate/${index}`)
  return data
}

export const moveWorkingPlateEntry = async (index: number, targetIndex: number): Promise<SettingsDocument> => {
  const { data } = await api.post<SettingsDocument>(`/settings/working-plate/${index}/move`, {
    target_index: targetIndex,
  })
  return data
}

export const fetchLabware = async (): Promise<LabwareDocument> => {
  const { data } = await api.get<LabwareDocument>('/labware')
  return data
}

export const fetchCsvList = async (): Promise<CsvListResponse> => {
  const { data } = await api.get<CsvListResponse>('/csvs')
  return data
}

export const fetchCsvContent = async (name: string): Promise<string> => {
  const { data } = await api.get<string>(`/csvs/${encodeURIComponent(name)}`, { responseType: 'text' })
  return data
}

export const uploadCsv = async (payload: CsvUploadPayload): Promise<{ name: string }> => {
  const { data } = await api.post<{ name: string }>('/csvs', payload)
  return data
}

export const deleteCsv = async (name: string): Promise<void> => {
  await api.delete(`/csvs/${encodeURIComponent(name)}`)
}

export const runWorkflow = async (payload: WorkflowRequest): Promise<WorkflowResponse> => {
  const { data } = await api.post<WorkflowResponse>('/workflow/generate', payload)
  return data
}

export default api
