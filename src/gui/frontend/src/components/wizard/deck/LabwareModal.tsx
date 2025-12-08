import { Modal, Select, Button, Stack, NumberInput, Switch } from '@mantine/core'
import { useEffect, useMemo, useState } from 'react'
import { useLabwareQuery, usePatchSetting } from '../../../api/hooks'
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
  const { data: labwareOptions } = useLabwareQuery()
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

  // Check if dual mode is enabled
  const isDualMode = state.settings?.settings?.general?.mode === 'dual'

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
    if (!labwareOptions?.labware) return []

    // Group labware by category
    const grouped: Record<string, Array<{ value: string; label: string }>> = {}

    labwareOptions.labware.forEach(l => {
      const category = l.category || 'other'
      if (!grouped[category]) grouped[category] = []
      grouped[category].push({
        value: l.labware_id,
        label: `${l.labware_id} (${l.well_count} wells, ${l.well_volume}µL)`
      })
    })

    // Convert to Mantine Select format with groups
    const selectData: Array<{ group: string; items: Array<{ value: string; label: string }> }> = []

    // Define preferred order for categories
    const categoryOrder = ['tip_rack', 'plate', 'tube_rack', 'reservoir']
    const categoryLabels: Record<string, string> = {
      tip_rack: 'Tip Racks',
      plate: 'Plates',
      tube_rack: 'Tube Racks',
      reservoir: 'Reservoirs',
      other: 'Other'
    }

    // Add groups in preferred order
    categoryOrder.forEach(cat => {
      if (grouped[cat]) {
        selectData.push({
          group: categoryLabels[cat] || cat,
          items: grouped[cat]
        })
      }
    })

    // Add remaining categories not in preferred order
    Object.keys(grouped).forEach(cat => {
      if (!categoryOrder.includes(cat)) {
        selectData.push({
          group: categoryLabels[cat] || cat,
          items: grouped[cat]
        })
      }
    })

    // Add current labware if not found in list
    if (labwareId && !labwareOptions.labware.find(l => l.labware_id === labwareId)) {
      selectData.unshift({
        group: 'Current Selection',
        items: [{ value: labwareId, label: labwareId }]
      })
    }

    return selectData
  }, [labwareOptions, labwareId])

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
          placeholder="Select labware definition..."
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
