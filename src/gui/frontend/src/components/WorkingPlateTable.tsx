import { ActionIcon, Group, NumberInput, Select, Table, Tooltip } from '@mantine/core'
import { IconArrowDown, IconArrowUp, IconTrash } from '@tabler/icons-react'
import type { LabwareEntry, WorkingPlateEntry } from '../api/types'

interface WorkingPlateTableProps {
  entries: WorkingPlateEntry[]
  labware: LabwareEntry[]
  onUpdate: (index: number, field: keyof WorkingPlateEntry, value: string | null) => void
  onRemove?: (index: number) => void
  onMove?: (index: number, direction: 'up' | 'down') => void
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

export function WorkingPlateTable({ entries, labware, onUpdate, onRemove, onMove }: WorkingPlateTableProps) {
  const labwareOptions = labware.map((lw) => ({
    value: lw.labware_id,
    label: `${lw.labware_id} (${lw.category})`,
  }))

  return (
    <Table striped highlightOnHover withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Type</Table.Th>
          <Table.Th>Labware</Table.Th>
          <Table.Th>Deck Slot</Table.Th>
          <Table.Th>Connection</Table.Th>
          <Table.Th style={{ width: 120 }}>Actions</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {entries.map((entry, index) => (
          <Table.Tr key={`${entry.labware_id ?? 'entry'}-${index}`}>
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
              />
            </Table.Td>
            <Table.Td>
              <Group gap="xs">
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
        ))}
      </Table.Tbody>
    </Table>
  )
}
