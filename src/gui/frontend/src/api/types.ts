export interface GeneralSettings {
  mode: 'multi' | 'multi_X1' | 'single_X1' | 'dual'
  starting_tip_well: string
  head_speed: {
    speed: number
  }
}

export interface PreAspirateContactSettings {
  enabled: boolean
  position_offset_percent: number
  aspirate_volume: number
}

export interface PostAspirateWickSettings {
  enabled: boolean
  radius: number
  v_offset_mm: number
  speed: number
}

export interface DelaySettings {
  post_aspirate: number
}

export interface PushOutSettings {
  enabled: boolean
  volume_ul: number
}

export interface MixingSettings {
  location: 'destination' | 'source' | 'none'
  repetitions: number
  source_remixing: 'once' | 'always'
}

export interface WorkingPlateEntry {
  type: string
  labware_id?: string
  position_rack?: string
  connection?: string
  mode?: 'multi' | 'multi_X1' | 'single_X1'
  module_type?: string
  target_temperature?: number
  target_shake_speed?: number
  persist_after_protocol?: boolean
}

export interface LiquidHandlingSettings {
  pre_aspirate_contact: PreAspirateContactSettings
  post_aspirate_wick: PostAspirateWickSettings
  delays: DelaySettings
  push_out: PushOutSettings
  mixing: MixingSettings
}

export interface SettingsDocument {
  settings: {
    general: GeneralSettings
    liquid_handling: LiquidHandlingSettings
    working_plate: WorkingPlateEntry[]
  }
}

export interface LabwareEntry {
  category: string
  labware_id: string
  well_count: number
  well_volume: number
  offset_x?: number
  offset_y?: number
  offset_z?: number
}

export interface LabwareDocument {
  pipettes?: unknown
  labware: LabwareEntry[]
}

export interface CsvListResponse {
  files: string[]
}

export interface CsvUploadPayload {
  name: string
  content: string
}

export interface WorkflowRequest {
  csv: string
  run_simulation?: boolean
  use_shell_runner?: boolean
  send_to_opentrons?: boolean
  target_path?: string
  copy_to_clipboard?: boolean
}

export interface SimulationResult {
  success?: boolean
  stdout?: string
  stderr?: string
  returncode?: number
  error?: string
  command?: string[]
}

export interface WorkflowResponse {
  generated: {
    protocol_file: string
    json_size: number
    message: string
  }
  simulation?: SimulationResult | null
  deployment?: {
    protocol_file: string
    copies: string[]
    clipboard?: Record<string, unknown> | null
  } | null
  logs: string[]
}

export interface ShellSettings {
  target_protocol_src_win?: string | null
  labware_path_win?: string | null
}

export interface ShellSettingsUpdate {
  target_protocol_src_win?: string
  labware_path_win?: string
}

export type ShellSettingsField = 'target_protocol_src_win' | 'labware_path_win'

export interface ShellSettingsBrowseRequest {
  field: ShellSettingsField
}
