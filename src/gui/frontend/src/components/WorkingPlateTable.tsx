import { Fragment, useState } from 'react'
import { ActionIcon, Group, NumberInput, Select, Stack, Switch, Table, Text, TextInput, Tooltip } from '@mantine/core'
import { IconArrowDown, IconArrowUp, IconSettings, IconTrash } from '@tabler/icons-react'
import type { LabwareEntry, WorkingPlateEntry } from '../api/types'

interface WorkingPlateTableProps {
  entries: WorkingPlateEntry[]
  labware: LabwareEntry[]
  onUpdate: (index: number, field: keyof WorkingPlateEntry, value: string | number | boolean | null) => void
  onRemove?: (index: number) => void
  onMove?: (index: number, direction: 'up' | 'down') => void
  generalMode?: string
}

const typeOptions = [
  { value: 'source', label: 'Source' },
  { value: 'destination', label: 'Destination' },
  { value: 'reservoir', label: 'Reservoir' },
  { value: 'tip', label: 'Tip Rack' },
  { value: 'module', label: 'Module' },
]

const connectionOptions = [
  { value: 'Pipette_8', label: 'Pipette_8 (multi)' },
  { value: 'Pipette_1', label: 'Pipette_1 (single)' },
]

const tipModeOptions = [
  { value: 'multi', label: 'Multi (8-tip)' },
  { value: 'multi_X1', label: 'Multi X1 (1-tip)' },
  { value: 'single_X1', label: 'Single X1' },
]

export function WorkingPlateTable({ entries, labware, onUpdate, onRemove, onMove, generalMode }: WorkingPlateTableProps) {
  const labwareOptions = labware.map((lw) => ({
    value: lw.labware_id,
    label: `${lw.labware_id} (${lw.category})`,
  }))
  const [expandedModules, setExpandedModules] = useState<Record<number, boolean>>({})

  const toggleModule = (index: number) => {
    setExpandedModules((prev) => ({ ...prev, [index]: !prev[index] }))
  }

  const isDualMode = generalMode === 'dual'

  return (
    <Table striped highlightOnHover withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Type</Table.Th>
          <Table.Th>Labware</Table.Th>
          <Table.Th>Deck Slot</Table.Th>
          <Table.Th>Connection</Table.Th>
          {isDualMode && <Table.Th>Tip Mode</Table.Th>}
          <Table.Th style={{ width: 120 }}>Actions</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {entries.map((entry, index) => (
          <Fragment key={`working-plate-${index}`}>
            <Table.Tr>
              <Table.Td>
                <Select
                  data={typeOptions}
                  value={entry.type}
                  onChange={(value) => value && onUpdate(index, 'type', value)}
                  placeholder="Type"
                />
              </Table.Td>
              <Table.Td>
                <Select
                  searchable
                  data={labwareOptions}
                  value={entry.labware_id ?? null}
                  placeholder="Select labware"
                  onChange={(value) => value && onUpdate(index, 'labware_id', value)}
                  disabled={entry.type === 'module'}
                />
              </Table.Td>
              <Table.Td>
                <NumberInput
                  value={entry.position_rack ? Number(entry.position_rack) : undefined}
                  placeholder="Slot"
                  min={1}
                  max={12}
                  onChange={(value) => {
                    if (value !== '') {
                      onUpdate(index, 'position_rack', String(value))
                    }
                  }}
                />
              </Table.Td>
              <Table.Td>
                <Select
                  data={connectionOptions}
                  value={entry.connection ?? null}
                  placeholder="Select pipette"
                  allowDeselect
                  clearable
                  onChange={(value) => onUpdate(index, 'connection', value ?? null)}
                  disabled={entry.type === 'module'}
                />
              </Table.Td>
              {isDualMode && (
                <Table.Td>
                  {entry.type === 'tip' ? (
                    <Select
                      data={tipModeOptions}
                      value={entry.mode ?? null}
                      placeholder="Select mode"
                      allowDeselect
                      clearable
                      onChange={(value) => onUpdate(index, 'mode', value ?? null)}
                    />
                  ) : (
                    <Text c="dimmed" size="sm">-</Text>
                  )}
                </Table.Td>
              )}
              <Table.Td>
                <Group gap="xs">
                  {entry.type === 'module' && (
                    <Tooltip label={expandedModules[index] ? 'Hide module settings' : 'Show module settings'}>
                      <ActionIcon variant="subtle" onClick={() => toggleModule(index)} aria-label="Toggle module settings">
                        <IconSettings size={16} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                  {onMove && (
                    <>
                      <Tooltip label="Move up">
                        <ActionIcon
                          variant="subtle"
                          disabled={index === 0}
                          onClick={() => onMove(index, 'up')}
                          aria-label="Move up"
                        >
                          <IconArrowUp size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="Move down">
                        <ActionIcon
                          variant="subtle"
                          disabled={index === entries.length - 1}
                          onClick={() => onMove(index, 'down')}
                          aria-label="Move down"
                        >
                          <IconArrowDown size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </>
                  )}
                  {onRemove && (
                    <Tooltip label="Remove labware">
                      <ActionIcon color="red" variant="light" onClick={() => onRemove(index)}>
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Group>
              </Table.Td>
            </Table.Tr>
            {entry.type === 'module' && expandedModules[index] && (
              <Table.Tr>
                <Table.Td colSpan={isDualMode ? 6 : 5}>
                  <Stack gap="xs">
                    <Text size="sm" c="dimmed">
                      Module settings
                    </Text>
                    <Group gap="md" align="flex-end">
                      <TextInput
                        label="Module type"
                        placeholder="heaterShaker"
                        value={entry.module_type ?? ''}
                        onChange={(event) => onUpdate(index, 'module_type', event.currentTarget.value)}
                      />
                      <NumberInput
                        label="Target temperature (°C)"
                        value={entry.target_temperature ?? 0}
                        min={0}
                        max={95}
                        onChange={(value) =>
                          value !== '' && onUpdate(index, 'target_temperature', Number(value))
                        }
                      />
                      <NumberInput
                        label="Shake speed (RPM)"
                        value={entry.target_shake_speed ?? 0}
                        min={0}
                        max={3000}
                        onChange={(value) =>
                          value !== '' && onUpdate(index, 'target_shake_speed', Number(value))
                        }
                      />
                      <Switch
                        label="Persist after protocol"
                        checked={entry.persist_after_protocol ?? false}
                        onChange={(event) =>
                          onUpdate(index, 'persist_after_protocol', event.currentTarget.checked)
                        }
                      />
                    </Group>
                  </Stack>
                </Table.Td>
              </Table.Tr>
            )}
          </Fragment>
        ))}
      </Table.Tbody>
    </Table>
  )
}
