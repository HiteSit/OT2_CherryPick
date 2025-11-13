import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { PatchPayload } from './client'
import {
  deleteCsv,
  deleteWorkingPlateEntry,
  fetchCsvContent,
  fetchCsvList,
  fetchLabware,
  fetchRawSettings,
  fetchSettings,
  addWorkingPlateEntry,
  moveWorkingPlateEntry,
  patchSetting,
  replaceSettings,
  runWorkflow,
  uploadCsv,
} from './client'
import type { CsvUploadPayload, WorkflowRequest } from './types'

export const useSettingsQuery = () =>
  useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  })

export const useRawSettingsQuery = () =>
  useQuery({
    queryKey: ['settings', 'raw'],
    queryFn: fetchRawSettings,
  })

export const useLabwareQuery = () =>
  useQuery({
    queryKey: ['labware'],
    queryFn: fetchLabware,
  })

export const useCsvListQuery = () =>
  useQuery({
    queryKey: ['csvs'],
    queryFn: fetchCsvList,
  })

export const useCsvContentQuery = (name?: string) =>
  useQuery({
    queryKey: ['csvs', name],
    queryFn: () => fetchCsvContent(name!),
    enabled: Boolean(name),
  })

export const usePatchSetting = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PatchPayload) => patchSetting(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['settings', 'raw'] })
    },
  })
}

export const useReplaceSettings = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: replaceSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['settings', 'raw'] })
    },
  })
}

export const useWorkflowRunner = () =>
  useMutation({
    mutationFn: (payload: WorkflowRequest) => runWorkflow(payload),
  })

export const useUploadCsv = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CsvUploadPayload) => uploadCsv(payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['csvs'] })
      queryClient.invalidateQueries({ queryKey: ['csvs', variables.name] })
    },
  })
}

export const useDeleteCsv = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => deleteCsv(name),
    onSuccess: (_, name) => {
      queryClient.invalidateQueries({ queryKey: ['csvs'] })
      queryClient.removeQueries({ queryKey: ['csvs', name] })
    },
  })
}

export const useAddWorkingPlateEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: addWorkingPlateEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}

export const useDeleteWorkingPlateEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (index: number) => deleteWorkingPlateEntry(index),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}

export const useMoveWorkingPlateEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ index, target }: { index: number; target: number }) => moveWorkingPlateEntry(index, target),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}
