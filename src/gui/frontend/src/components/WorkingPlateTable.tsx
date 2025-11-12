import { NumberInput, Select, Table, TextInput } from '@mantine/core'
import type { LabwareEntry, WorkingPlateEntry } from '../api/types'

interface WorkingPlateTableProps {
  entries: WorkingPlateEntry[]
  labware: LabwareEntry[]
  onUpdate: (index: number, field: keyof WorkingPlateEntry, value: string) => void
}

const typeOptions = [
  { value: 'source', label: 'Source' },
  { value: 'destination', label: 'Destination' },
  { value: 'reservoir', label: 'Reservoir' },
  { value: 'tip', label: 'Tip Rack' },
  { value: 'module', label: 'Module' },
]

export function WorkingPlateTable({ entries, labware, onUpdate }: WorkingPlateTableProps) {
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
              <TextInput
                value={entry.connection ?? ''}
                placeholder="Pipette"
                onChange={(event) => onUpdate(index, 'connection', event.currentTarget.value)}
              />
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}
