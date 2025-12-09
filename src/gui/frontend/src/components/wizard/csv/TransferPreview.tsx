import { Stack, Title, Text, Paper, Button, ScrollArea } from '@mantine/core'
import Papa from 'papaparse'

interface TransferRow {
  'Source Labware'?: string
  'Source Well'?: string
  'Volume (ul)'?: string
  'Distribution Volume (ul)'?: string
  'Distribution'?: string
  'Dest Labware'?: string
  'Dest Well'?: string
  [key: string]: string | undefined
}

export function TransferPreview({ csvContent }: { csvContent: string }) {
  if (!csvContent) {
    return (
      <Paper withBorder p="md">
        <Text size="sm" c="dimmed">
          No transfers to preview. Upload or create a CSV file.
        </Text>
      </Paper>
    )
  }

  const parsed = Papa.parse<TransferRow>(csvContent, { header: true })
  const rows = parsed.data.filter(row => row['Source Labware'] || row['Dest Labware'])
  const previewRows = rows.slice(0, 5)

  return (
    <Stack gap="md">
      <Title order={5}>Transfer Preview</Title>
      <Text size="xs" c="dimmed">
        Showing first 5 of {rows.length} transfers
      </Text>

      <ScrollArea h={400}>
        <Stack gap="xs">
          {previewRows.map((row, i) => {
            // Detect distribution row
            const destWell = row['Dest Well'] || ''
            const hasPipe = destWell.includes('|')
            const hasDistVolume = !!row['Distribution Volume (ul)']
            const isDistribution = hasPipe || hasDistVolume

            const volume = isDistribution ? row['Distribution Volume (ul)'] : row['Volume (ul)']
            const wellCount = hasPipe ? destWell.split('|').length : 1

            return (
              <Paper key={i} withBorder p="xs" style={{ fontSize: '0.85rem' }}>
                <Text size="sm" fw={500} mb={4}>
                  Transfer {i + 1}
                  {isDistribution && <Text span c="dimmed" ml={4}>(Distribution)</Text>}
                </Text>
                <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>
                  {row['Source Labware']} [{row['Source Well']}]
                </Text>
                <Text size="xs" c="blue" style={{ fontFamily: 'monospace' }}>
                  → {row['Dest Labware']} [{row['Dest Well']}]
                </Text>
                {isDistribution ? (
                  <Text size="xs" fw={500} mt={4} c="grape">
                    Dist: {volume}µL × {wellCount} wells
                    {row['Distribution'] && ` (${row['Distribution']})`}
                  </Text>
                ) : (
                  <Text size="xs" fw={500} mt={4}>
                    Vol: {volume}µL
                  </Text>
                )}
                {row['Mix Volume'] && (
                  <Text size="xs" c="dimmed">
                    Mix: {row['Mix Volume']}µL
                  </Text>
                )}
              </Paper>
            )
          })}
        </Stack>
      </ScrollArea>

      {rows.length > 5 && (
        <Button variant="subtle" size="xs" fullWidth>
          {rows.length - 5} more transfers...
        </Button>
      )}

      {rows.length === 0 && (
        <Text size="sm" c="dimmed" ta="center">
          No valid transfers found in CSV
        </Text>
      )}
    </Stack>
  )
}
