import { Loader, Table, Text } from '@mantine/core'
import { useLabwareQuery } from '../api/hooks'

export function LabwareSummary() {
  const { data, isLoading } = useLabwareQuery()

  if (isLoading || !data) {
    return (
      <Text c="dimmed" size="sm">
        <Loader size="xs" /> Loading labware catalog...
      </Text>
    )
  }

  return (
    <Table striped highlightOnHover withTableBorder>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>ID</Table.Th>
          <Table.Th>Category</Table.Th>
          <Table.Th>Volume (µL)</Table.Th>
          <Table.Th>Wells</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {data.labware.map((entry) => (
          <Table.Tr key={entry.labware_id}>
            <Table.Td>{entry.labware_id}</Table.Td>
            <Table.Td>{entry.category}</Table.Td>
            <Table.Td>{entry.well_volume}</Table.Td>
            <Table.Td>{entry.well_count}</Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}
