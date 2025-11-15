import { Stack, Badge, Alert, Button, Group, ScrollArea, Text } from '@mantine/core'
import { IconCheck, IconAlertTriangle, IconX } from '@tabler/icons-react'
import { useState } from 'react'
import Papa from 'papaparse'
import type { WorkingPlateEntry } from '../../../api/types'

interface ValidationResult {
  type: 'valid' | 'warning' | 'error'
  message: string
  row?: number
}

interface ValidationPanelProps {
  csvContent: string
  deckLayout: WorkingPlateEntry[]
}

export function ValidationPanel({ csvContent, deckLayout }: ValidationPanelProps) {
  const [results, setResults] = useState<ValidationResult[]>([])
  const [validated, setValidated] = useState(false)

  const handleValidate = () => {
    const parsed = Papa.parse(csvContent, { header: true })
    const newResults: ValidationResult[] = []

    // Basic validation
    if (!csvContent) {
      newResults.push({ type: 'error', message: 'No CSV content to validate' })
      setResults(newResults)
      setValidated(true)
      return
    }

    newResults.push({ type: 'valid', message: 'CSV format is valid' })

    // Check required columns
    const headers = parsed.meta.fields || []
    const required = ['Source Labware', 'Source Well', 'Volume (ul)', 'Dest Labware', 'Dest Well']
    const missing = required.filter(r => !headers.includes(r))

    if (missing.length > 0) {
      newResults.push({ type: 'error', message: `Missing required columns: ${missing.join(', ')}` })
    } else {
      newResults.push({ type: 'valid', message: 'All required columns present' })
    }

    // Check for height column conflicts
    const hasSourceHeight = headers.includes('Source Height')
    const hasSourceTop = headers.includes('Source Top')
    const hasDestHeight = headers.includes('Dest Height')
    const hasDestTop = headers.includes('Dest Top')

    if (hasSourceHeight && hasSourceTop) {
      newResults.push({ type: 'warning', message: 'Both "Source Height" and "Source Top" columns found. Use only one.' })
    }
    if (hasDestHeight && hasDestTop) {
      newResults.push({ type: 'warning', message: 'Both "Dest Height" and "Dest Top" columns found. Use only one.' })
    }

    // Create labware reference map
    const deckLabwareIds = new Set(
      deckLayout
        .filter(l => l.labware_id && l.position_rack)
        .map(l => `${l.labware_id}_${l.position_rack}`)
    )

    // Check labware references and volumes
    const rows = parsed.data as any[]
    let validTransfers = 0

    rows.forEach((row, i) => {
      const sourceLab = row['Source Labware']
      const destLab = row['Dest Labware']
      const volume = row['Volume (ul)']

      // Skip empty rows
      if (!sourceLab && !destLab && !volume) return

      validTransfers++

      if (sourceLab && !deckLabwareIds.has(sourceLab)) {
        newResults.push({
          type: 'error',
          message: `Source labware "${sourceLab}" not found in deck layout`,
          row: i + 2
        })
      }

      if (destLab && !deckLabwareIds.has(destLab)) {
        newResults.push({
          type: 'error',
          message: `Dest labware "${destLab}" not found in deck layout`,
          row: i + 2
        })
      }

      // Volume validation
      if (volume && (isNaN(parseFloat(volume)) || parseFloat(volume) <= 0)) {
        newResults.push({
          type: 'error',
          message: `Invalid volume: ${volume}`,
          row: i + 2
        })
      }

      // Well format validation (basic)
      const sourceWell = row['Source Well']
      const destWell = row['Dest Well']

      if (sourceWell && !/^[A-H]\d{1,2}$/i.test(sourceWell)) {
        newResults.push({
          type: 'warning',
          message: `Source well "${sourceWell}" may have invalid format (expected: A1-H12)`,
          row: i + 2
        })
      }

      if (destWell && !/^[A-P]\d{1,2}$/i.test(destWell)) {
        newResults.push({
          type: 'warning',
          message: `Dest well "${destWell}" may have invalid format`,
          row: i + 2
        })
      }
    })

    if (validTransfers === 0) {
      newResults.push({ type: 'error', message: 'No valid transfers found in CSV' })
    } else {
      newResults.push({ type: 'valid', message: `${validTransfers} transfer rows found` })
    }

    setResults(newResults)
    setValidated(true)
  }

  const valid = results.filter(r => r.type === 'valid').length
  const warnings = results.filter(r => r.type === 'warning')
  const errors = results.filter(r => r.type === 'error')

  const hasErrors = errors.length > 0

  return (
    <Stack gap="md">
      <Button onClick={handleValidate} variant="light" fullWidth>
        Validate CSV
      </Button>

      {validated && (
        <>
          <Group>
            <Badge color="green" leftSection={<IconCheck size={14} />}>
              {valid} valid
            </Badge>
            <Badge color="orange" leftSection={<IconAlertTriangle size={14} />}>
              {warnings.length} warnings
            </Badge>
            <Badge color="red" leftSection={<IconX size={14} />}>
              {errors.length} errors
            </Badge>
          </Group>

          <ScrollArea h={300}>
            <Stack gap="xs">
              {errors.map((err, i) => (
                <Alert key={`err-${i}`} color="red" variant="light" p="xs">
                  <Text size="xs">
                    {err.row && `Row ${err.row}: `}{err.message}
                  </Text>
                </Alert>
              ))}
              {warnings.map((warn, i) => (
                <Alert key={`warn-${i}`} color="orange" variant="light" p="xs">
                  <Text size="xs">
                    {warn.row && `Row ${warn.row}: `}{warn.message}
                  </Text>
                </Alert>
              ))}
            </Stack>
          </ScrollArea>

          {!hasErrors && errors.length === 0 && warnings.length === 0 && (
            <Alert color="green" icon={<IconCheck size={16} />}>
              CSV validation passed! Ready to proceed.
            </Alert>
          )}
        </>
      )}
    </Stack>
  )
}
