import { Modal, Select, Button, Stack, NumberInput, Switch } from '@mantine/core'
import { useEffect, useMemo, useState } from 'react'
import { useAvailableLabwareQuery, useOffsetDatabaseQuery, useSaveOffsetMutation, usePatchSetting } from '../../../api/hooks'
import { useWizard } from '../WizardContext'
import type { WorkingPlateEntry } from '../../../api/types'

interface LabwareModalProps {
  opened: boolean
  onClose: () => void
  slot: number
  existingLabware?: WorkingPlateEntry
}

export function LabwareModal({ opened, onClose, slot, existingLabware }: LabwareModalProps) {
  const { state, setDeckLayout } = useWizard()
  const { data: availableLabware } = useAvailableLabwareQuery()
  const { data: offsetDb } = useOffsetDatabaseQuery()
  const saveOffsetMutation = useSaveOffsetMutation()
  const patchSettings = usePatchSetting()

  const normalizeModuleType = (value: string | undefined) => {
    if (!value) return ''
    if (value === 'heaterShaker' || value === 'heater_shaker') return 'heaterShaker'
    return value
  }
  const normalizeType = (value: string | undefined) => {
    const allowed = ['source', 'destination', 'tip', 'reservoir', 'module']
    return value && allowed.includes(value) ? value : 'source'
  }

  const [type, setType] = useState<string>(normalizeType(existingLabware?.type))
  const [labwareId, setLabwareId] = useState<string>(existingLabware?.labware_id || '')
  const [connection, setConnection] = useState<string>(existingLabware?.connection || '')
  const [tipMode, setTipMode] = useState<string>(existingLabware?.mode || '')
  const [moduleType, setModuleType] = useState<string>(normalizeModuleType(existingLabware?.module_type))
  const [targetTemperature, setTargetTemperature] = useState<number | string>(
    existingLabware?.target_temperature ?? ''
  )
  const [targetShakeSpeed, setTargetShakeSpeed] = useState<number | string>(
    existingLabware?.target_shake_speed ?? ''
  )
  const [persistAfterProtocol, setPersistAfterProtocol] = useState<boolean>(
    existingLabware?.persist_after_protocol ?? false
  )
  const [offsetX, setOffsetX] = useState<number | string>(existingLabware?.offset_x ?? '')
  const [offsetY, setOffsetY] = useState<number | string>(existingLabware?.offset_y ?? '')
  const [offsetZ, setOffsetZ] = useState<number | string>(existingLabware?.offset_z ?? '')
  const [saveOffsetToDb, setSaveOffsetToDb] = useState<boolean>(false)

  // Check if dual mode is enabled
  const isDualMode = state.settings?.settings?.general?.mode === 'dual'

  // Pre-populate offsets from offset database when labwareId or slot changes
  useEffect(() => {
    if (!labwareId || !offsetDb?.offsets) return
    const dbEntry = offsetDb.offsets.find(
      e => e.labware_id === labwareId && String(e.position_rack) === String(slot)
    )
    if (dbEntry && !existingLabware?.offset_x && !existingLabware?.offset_y && !existingLabware?.offset_z) {
      setOffsetX(dbEntry.offset_x)
      setOffsetY(dbEntry.offset_y)
      setOffsetZ(dbEntry.offset_z)
    }
  }, [labwareId, slot, offsetDb])

  // Re-sync when opening a different labware card; prevents stale state and crashes
  useEffect(() => {
    setType(normalizeType(existingLabware?.type))
    setLabwareId(existingLabware?.labware_id || '')
    setConnection(existingLabware?.connection || '')
    setTipMode(existingLabware?.mode || '')
    setModuleType(normalizeModuleType(existingLabware?.module_type))
    setTargetTemperature(existingLabware?.target_temperature ?? '')
    setTargetShakeSpeed(existingLabware?.target_shake_speed ?? '')
    setPersistAfterProtocol(existingLabware?.persist_after_protocol ?? false)
    setOffsetX(existingLabware?.offset_x ?? '')
    setOffsetY(existingLabware?.offset_y ?? '')
    setOffsetZ(existingLabware?.offset_z ?? '')
    setSaveOffsetToDb(false)
  }, [existingLabware])

  const handleSave = () => {
    const newEntry: WorkingPlateEntry = {
      type,
      position_rack: String(slot),
    }

    // Add labware_id only if it's set (optional for modules)
    if (labwareId) {
      newEntry.labware_id = labwareId
    }

    // Add optional fields for tip racks
    if (type === 'tip') {
      if (connection) {
        newEntry.connection = connection
      }
      // Add mode field when in dual mode (required for tip allocation per CSV Mode column)
      if (isDualMode && tipMode) {
        newEntry.mode = tipMode as 'multi' | 'multi_X1' | 'single_X1'
      }
    }
    if (type === 'module') {
      if (moduleType) newEntry.module_type = moduleType
      // Hardcode adapter_id for heater-shaker modules
      if (moduleType === 'heaterShaker') {
        newEntry.adapter_id = 'opentrons_universal_flat_adapter'
      }
      if (typeof targetTemperature === 'number') {
        newEntry.target_temperature = targetTemperature
      }
      if (typeof targetShakeSpeed === 'number') {
        newEntry.target_shake_speed = targetShakeSpeed
      }
      newEntry.persist_after_protocol = persistAfterProtocol
    }

    // Add offsets if set
    if (typeof offsetX === 'number') newEntry.offset_x = offsetX
    if (typeof offsetY === 'number') newEntry.offset_y = offsetY
    if (typeof offsetZ === 'number') newEntry.offset_z = offsetZ

    // Optionally save offsets to database
    if (saveOffsetToDb && labwareId && (typeof offsetX === 'number' || typeof offsetY === 'number' || typeof offsetZ === 'number')) {
      saveOffsetMutation.mutate({
        labware_id: labwareId,
        position_rack: String(slot),
        offset_x: typeof offsetX === 'number' ? offsetX : 0,
        offset_y: typeof offsetY === 'number' ? offsetY : 0,
        offset_z: typeof offsetZ === 'number' ? offsetZ : 0,
      })
    }

    const existingIndex = state.deckLayout.findIndex(item => item.position_rack === String(slot))
    const updatedLayout =
      existingIndex >= 0
        ? state.deckLayout.map(item => (item.position_rack === String(slot) ? newEntry : item))
        : [...state.deckLayout, newEntry]

    setDeckLayout(updatedLayout)
    patchSettings.mutate({ path: 'settings.working_plate', value: updatedLayout })

    onClose()
  }

  const labwareSelectData = useMemo(() => {
    if (!availableLabware) return []

    // Group by source: Custom first, then Official
    const custom = availableLabware.filter(l => l.source === 'custom')
    const official = availableLabware.filter(l => l.source === 'official')

    const selectData: Array<{ group: string; items: Array<{ value: string; label: string }> }> = []

    if (custom.length > 0) {
      selectData.push({
        group: 'Custom Labware',
        items: custom.map(l => ({
          value: l.labware_id,
          label: l.well_count != null
            ? `${l.display_name} (${l.well_count} wells)`
            : l.display_name,
        }))
      })
    }

    if (official.length > 0) {
      selectData.push({
        group: 'Official Opentrons',
        items: official.map(l => ({
          value: l.labware_id,
          label: l.labware_id,
        }))
      })
    }

    // Add current labware if not found in list
    const allIds = availableLabware.map(l => l.labware_id)
    if (labwareId && !allIds.includes(labwareId)) {
      selectData.unshift({
        group: 'Current Selection',
        items: [{ value: labwareId, label: labwareId }]
      })
    }

    return selectData
  }, [availableLabware, labwareId])

  const showOffsets = type !== 'module'

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={existingLabware ? `Edit Labware - Slot ${slot}` : `Add Labware - Slot ${slot}`}
      size="lg"
    >
      <Stack gap="md">
        <Select
          label="Type"
          data={[
            { value: 'source', label: 'Source' },
            { value: 'destination', label: 'Destination' },
            { value: 'tip', label: 'Tip Rack' },
            { value: 'reservoir', label: 'Reservoir' },
            { value: 'module', label: 'Module' },
          ]}
          value={type}
          onChange={(v) => setType(v || 'source')}
          required
        />

        <Select
          label="Labware"
          placeholder="Select labware..."
          data={labwareSelectData}
          value={labwareId}
          onChange={(v) => setLabwareId(v || '')}
          searchable
          required={type !== 'module'}
          maxDropdownHeight={400}
        />

        {type === 'tip' && (
          <>
            <Select
              label="Pipette Connection"
              description="Which pipette will use these tips"
              data={[
                { value: 'Pipette_1', label: 'Pipette 1 (Single Channel)' },
                { value: 'Pipette_8', label: 'Pipette 8 (Multi Channel)' },
              ]}
              value={connection}
              onChange={(v) => setConnection(v || '')}
            />
            {isDualMode && (
              <Select
                label="Tip Mode"
                description="Which transfer mode uses this tip rack (required in dual mode)"
                data={[
                  { value: 'multi', label: 'Multi (8-tip)' },
                  { value: 'multi_X1', label: 'Multi X1 (1-tip from 8-channel)' },
                  { value: 'single_X1', label: 'Single X1 (1-channel pipette)' },
                ]}
                value={tipMode}
                onChange={(v) => setTipMode(v || '')}
                required
              />
            )}
          </>
        )}

        {type === 'module' && (
          <>
            <Select
              label="Module Type"
              data={[
                { value: 'heaterShaker', label: 'Heater Shaker' },
              ]}
              value={moduleType}
              onChange={(v) => setModuleType(v || '')}
            />

            {(moduleType === 'temperature' || moduleType === 'thermocycler' || moduleType === 'heaterShaker') && (
              <NumberInput
                label="Target Temperature (°C)"
                description="Temperature to maintain during protocol"
                value={typeof targetTemperature === 'number' ? targetTemperature : undefined}
                onChange={setTargetTemperature}
                min={30}
                max={95}
              />
            )}

            {moduleType === 'heaterShaker' && (
              <NumberInput
                label="Target Shake Speed (RPM)"
                description="Shaking speed during protocol"
                value={typeof targetShakeSpeed === 'number' ? targetShakeSpeed : undefined}
                onChange={setTargetShakeSpeed}
                min={200}
                max={3000}
              />
            )}

            <Switch
              label="Persist after protocol"
              description="Keep module settings active after protocol ends"
              checked={persistAfterProtocol}
              onChange={(e) => setPersistAfterProtocol(e.currentTarget.checked)}
            />
          </>
        )}

        {showOffsets && (
          <>
            <NumberInput
              label="Offset X (mm)"
              description="Left/right adjustment: negative=left, positive=right"
              value={typeof offsetX === 'number' ? offsetX : undefined}
              onChange={setOffsetX}
              decimalScale={2}
              step={0.1}
            />
            <NumberInput
              label="Offset Y (mm)"
              description="Front/back adjustment: negative=front, positive=back"
              value={typeof offsetY === 'number' ? offsetY : undefined}
              onChange={setOffsetY}
              decimalScale={2}
              step={0.1}
            />
            <NumberInput
              label="Offset Z (mm)"
              description="Height adjustment: negative=down, positive=up"
              value={typeof offsetZ === 'number' ? offsetZ : undefined}
              onChange={setOffsetZ}
              decimalScale={2}
              step={0.1}
            />
            <Switch
              label="Save offset to database"
              description="Persist this offset in offset_database.toml for future protocols"
              checked={saveOffsetToDb}
              onChange={(e) => setSaveOffsetToDb(e.currentTarget.checked)}
            />
          </>
        )}

        <Button
          onClick={handleSave}
          disabled={type !== 'module' && !labwareId}
          loading={patchSettings.isPending}
        >
          {existingLabware ? 'Update' : 'Add'} Labware
        </Button>
      </Stack>
    </Modal>
  )
}
