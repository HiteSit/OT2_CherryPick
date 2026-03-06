export interface GeneralSettings {
  protocol_name?: string
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
  enabled: boolean
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
  adapter_id?: string
  target_temperature?: number
  target_shake_speed?: number
  persist_after_protocol?: boolean
  offset_x?: number
  offset_y?: number
  offset_z?: number
}

export interface LiquidHandlingPreset {
  pre_aspirate_contact: PreAspirateContactSettings
  post_aspirate_wick: PostAspirateWickSettings
  delays: DelaySettings
  push_out: PushOutSettings
  mixing: MixingSettings
}

export interface LiquidHandlingSettings {
  active_preset: string
  pre_aspirate_contact: PreAspirateContactSettings
  post_aspirate_wick: PostAspirateWickSettings
  delays: DelaySettings
  push_out: PushOutSettings
  mixing: MixingSettings
  presets?: Record<string, LiquidHandlingPreset>
}

export interface SettingsDocument {
  settings: {
    general: GeneralSettings
    liquid_handling: LiquidHandlingSettings
    working_plate: WorkingPlateEntry[]
  }
}

export interface AvailableLabware {
  labware_id: string
  well_count: number | null
  display_name: string
  display_category: string
  source: 'custom' | 'official'
}

export interface OffsetEntry {
  labware_id: string
  position_rack: string
  offset_x: number
  offset_y: number
  offset_z: number
  last_calibrated?: string
  notes?: string
}

export interface OffsetDatabase {
  offsets?: OffsetEntry[]
}

export interface PipetteEntry {
  name: string
  opentrons_id: string
  channels: number
  volume_range: [number, number]
  preferred_mount: 'left' | 'right'
  tip_connections: string[]
}

export interface LabwareDocument {
  pipettes: PipetteEntry[]
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
  opentrons_dir_win?: string | null
}

export interface ShellSettingsUpdate {
  opentrons_dir_win?: string
}

export type ShellSettingsField = 'opentrons_dir_win'

export interface ShellSettingsBrowseRequest {
  field: ShellSettingsField
}
