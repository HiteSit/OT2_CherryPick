import { Modal, Select, Button, Stack, NumberInput, Switch } from '@mantine/core'
import { useState } from 'react'
import { useLabwareQuery, useAddWorkingPlateEntry } from '../../../api/hooks'
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
  const addMutation = useAddWorkingPlateEntry()

  // Form state - initialize from existingLabware or defaults
  const [type, setType] = useState<string>(existingLabware?.type || 'source')
  const [labwareId, setLabwareId] = useState<string>(existingLabware?.labware_id || '')
  const [connection, setConnection] = useState<string>(existingLabware?.connection || '')
  const [moduleType, setModuleType] = useState<string>(existingLabware?.module_type || '')
  const [targetTemperature, setTargetTemperature] = useState<number | string>(
    existingLabware?.target_temperature ?? ''
  )
  const [targetShakeSpeed, setTargetShakeSpeed] = useState<number | string>(
    existingLabware?.target_shake_speed ?? ''
  )
  const [persistAfterProtocol, setPersistAfterProtocol] = useState<boolean>(
    existingLabware?.persist_after_protocol ?? false
  )

  const handleSave = () => {
    const newEntry: WorkingPlateEntry = {
      type,
      labware_id: labwareId,
      position_rack: String(slot),
    }

    // Add optional fields
    if (type === 'tip' && connection) {
      newEntry.connection = connection
    }
    if (type === 'module') {
      if (moduleType) newEntry.module_type = moduleType
      if (typeof targetTemperature === 'number') {
        newEntry.target_temperature = targetTemperature
      }
      if (typeof targetShakeSpeed === 'number') {
        newEntry.target_shake_speed = targetShakeSpeed
      }
      newEntry.persist_after_protocol = persistAfterProtocol
    }

    if (existingLabware) {
      // Update existing labware
      const updatedLayout = state.deckLayout.map(item =>
        item.position_rack === String(slot) ? newEntry : item
      )
      setDeckLayout(updatedLayout)
    } else {
      // Add new labware
      setDeckLayout([...state.deckLayout, newEntry])
    }

    // Also update backend via mutation
    addMutation.mutate(newEntry)

    onClose()
  }

  const labwareSelectData = labwareOptions?.labware.map(l => ({
    value: l.labware_id,
    label: `${l.labware_id} (${l.well_count} wells, ${l.well_volume}µL)`,
  })) || []

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
          required
        />

        {type === 'tip' && (
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
        )}

        {type === 'module' && (
          <>
            <Select
              label="Module Type"
              data={[
                { value: 'temperature', label: 'Temperature Module' },
                { value: 'thermocycler', label: 'Thermocycler' },
                { value: 'heater_shaker', label: 'Heater Shaker' },
                { value: 'magnetic', label: 'Magnetic Module' },
              ]}
              value={moduleType}
              onChange={(v) => setModuleType(v || '')}
            />

            {(moduleType === 'temperature' || moduleType === 'thermocycler' || moduleType === 'heater_shaker') && (
              <NumberInput
                label="Target Temperature (°C)"
                description="Temperature to maintain during protocol"
                value={targetTemperature}
                onChange={setTargetTemperature}
                min={4}
                max={95}
              />
            )}

            {moduleType === 'heater_shaker' && (
              <NumberInput
                label="Target Shake Speed (RPM)"
                description="Shaking speed during protocol"
                value={targetShakeSpeed}
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
          disabled={!labwareId}
          loading={addMutation.isPending}
        >
          {existingLabware ? 'Update' : 'Add'} Labware
        </Button>
      </Stack>
    </Modal>
  )
}
