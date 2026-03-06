import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { PatchPayload } from './client'
import {
  addPipetteEntry,
  addWorkingPlateEntry,
  deleteCsv,
  deletePipetteEntry,
  deletePreset,
  deleteWorkingPlateEntry,
  fetchAvailableLabware,
  fetchCsvContent,
  fetchCsvList,
  fetchLabware,
  fetchOffsetDatabase,
  fetchRawSettings,
  fetchSettings,
  fetchShellSettings,
  moveWorkingPlateEntry,
  patchSetting,
  replaceSettings,
  runWorkflow,
  saveOffset,
  savePreset,
  updatePipetteEntry,
  updateShellSettings,
  uploadCsv,
} from './client'
import type {
  CsvUploadPayload,
  LiquidHandlingPreset,
  OffsetEntry,
  PipetteEntry,
  ShellSettingsUpdate,
  WorkflowRequest,
} from './types'

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

export const useAvailableLabwareQuery = () =>
  useQuery({
    queryKey: ['labware', 'available'],
    queryFn: fetchAvailableLabware,
  })

export const useOffsetDatabaseQuery = () =>
  useQuery({
    queryKey: ['labware', 'offsets'],
    queryFn: fetchOffsetDatabase,
  })

export const useSaveOffsetMutation = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: Omit<OffsetEntry, 'last_calibrated'>) => saveOffset(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labware', 'offsets'] })
    },
  })
}

export const useAddPipetteEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PipetteEntry) => addPipetteEntry(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labware'] })
    },
  })
}

export const useUpdatePipetteEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ index, payload }: { index: number; payload: PipetteEntry }) => updatePipetteEntry(index, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labware'] })
    },
  })
}

export const useDeletePipetteEntry = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (index: number) => deletePipetteEntry(index),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['labware'] })
    },
  })
}

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

export const useSavePreset = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, preset }: { name: string; preset: LiquidHandlingPreset }) => savePreset(name, preset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['settings', 'raw'] })
    },
  })
}

export const useDeletePreset = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => deletePreset(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      queryClient.invalidateQueries({ queryKey: ['settings', 'raw'] })
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

export const useShellSettingsQuery = () =>
  useQuery({
    queryKey: ['shell-settings'],
    queryFn: fetchShellSettings,
  })

export const useUpdateShellSettings = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: ShellSettingsUpdate) => updateShellSettings(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shell-settings'] })
    },
  })
}

