import { Stack, Badge, Alert, Button, Group, ScrollArea, Text } from '@mantine/core'
import { IconCheck, IconAlertTriangle, IconX } from '@tabler/icons-react'
import { useState } from 'react'
import Papa from 'papaparse'
import type { WorkingPlateEntry } from '../../../api/types'
import { useWizard } from '../WizardContext'

interface ValidationResult {
  type: 'valid' | 'warning' | 'error'
  message: string
  row?: number
}

// Check if a CSV row is a HOME control row (all non-empty values are "HOME")
function isHomeControlRow(row: Record<string, string>): boolean {
  const values = Object.values(row)
    .map(v => String(v ?? '').trim().toUpperCase())
    .filter(v => v.length > 0)
  return values.length > 0 && values.every(v => v === 'HOME')
}

interface ValidationPanelProps {
  csvContent: string
  deckLayout: WorkingPlateEntry[]
}

export function ValidationPanel({ csvContent, deckLayout }: ValidationPanelProps) {
  const { state } = useWizard()
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
    const baseRequired = ['Source Labware', 'Source Well', 'Dest Labware', 'Dest Well']
    const volumeColumns = ['Volume (ul)', 'Distribution Volume (ul)']

    const missingBase = baseRequired.filter(r => !headers.includes(r))
    const hasVolumeColumn = volumeColumns.some(v => headers.includes(v))

    if (missingBase.length > 0) {
      newResults.push({ type: 'error', message: `Missing required columns: ${missingBase.join(', ')}` })
    } else if (!hasVolumeColumn) {
      newResults.push({ type: 'error', message: `Must have at least one volume column: ${volumeColumns.join(' or ')}` })
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
    let hasAnyDistributionRow = false

    rows.forEach((row, i) => {
      const sourceLab = row['Source Labware']
      const destLab = row['Dest Labware']
      const destWell = row['Dest Well'] || ''

      // Detect distribution row (pipe in Dest Well or Distribution Volume present)
      const hasPipe = destWell.includes('|')
      const hasDistVolume = !!row['Distribution Volume (ul)']
      const isDistribution = hasPipe || hasDistVolume
      if (isDistribution) hasAnyDistributionRow = true

      const volume = isDistribution ? row['Distribution Volume (ul)'] : row['Volume (ul)']

      // Skip empty rows
      if (!sourceLab && !destLab && !volume) return

      // Skip HOME control rows from labware/volume validation
      // (they are special control commands, not actual transfers)
      if (isHomeControlRow(row)) return

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

      // Volume validation - check appropriate column based on row type
      if (volume && (isNaN(parseFloat(volume)) || parseFloat(volume) <= 0)) {
        newResults.push({
          type: 'error',
          message: `Invalid ${isDistribution ? 'distribution ' : ''}volume: ${volume}`,
          row: i + 2
        })
      } else if (!volume && (isDistribution ? hasDistVolume : row['Volume (ul)'] !== undefined)) {
        newResults.push({
          type: 'error',
          message: `Missing ${isDistribution ? 'distribution ' : ''}volume`,
          row: i + 2
        })
      }

      // Validate Distribution pattern if present
      if (isDistribution && row['Distribution']) {
        const distPattern = row['Distribution']
        if (!/^(equal|geometric:\d+(\.\d+)?(:(asc|desc))?)$/i.test(distPattern)) {
          newResults.push({
            type: 'warning',
            message: `Distribution pattern "${distPattern}" has unexpected format`,
            row: i + 2
          })
        }
      }

      // Well format validation
      const sourceWell = row['Source Well']

      if (sourceWell && !/^[A-P]\d{1,2}$/i.test(sourceWell)) {
        newResults.push({
          type: 'warning',
          message: `Source well "${sourceWell}" may have invalid format (expected: A1-P24)`,
          row: i + 2
        })
      }

      // Dest Well can be single well or pipe-delimited (A1|B1|C1)
      if (destWell) {
        const singleWellPattern = /^[A-P]\d{1,2}$/i
        const pipeDelimitedPattern = /^[A-P]\d{1,2}(\|[A-P]\d{1,2})*$/i

        if (!singleWellPattern.test(destWell) && !pipeDelimitedPattern.test(destWell)) {
          newResults.push({
            type: 'warning',
            message: `Dest well "${destWell}" may have invalid format`,
            row: i + 2
          })
        }
      }

      // Multi-channel distribution validation
      // In multi mode, all destination wells must have the same row letter
      const currentMode = state.settings?.settings?.general?.mode
      if (hasPipe && currentMode === 'multi') {
        const wellNames = destWell.split('|').map((w: string) => w.trim().toUpperCase())
        const rowLetters = new Set(
          wellNames
            .filter((w: string) => w.length > 0)
            .map((w: string) => w.replace(/\d+/g, ''))  // Extract row letter(s)
        )

        if (rowLetters.size > 1) {
          const sortedLetters = Array.from(rowLetters).sort().join(', ')
          newResults.push({
            type: 'error',
            message: `Distribution wells "${destWell}" incompatible with multi-channel mode. Found mixed row letters: ${sortedLetters}. In multi mode, all wells must have the SAME row letter (e.g., A1|A2|A3 or B1|B2|B3).`,
            row: i + 2
          })
        }
      }

      // HOME control row validation
      // Row after HOME MUST have Tip Action: new (firmware requirement)
      if (i > 0) {
        const prevRow = rows[i - 1] as Record<string, string>
        if (isHomeControlRow(prevRow) && !isHomeControlRow(row)) {
          const tipAction = (row['Tip Action'] || '').trim().toLowerCase()
          if (tipAction !== 'new') {
            newResults.push({
              type: 'error',
              message: `Row after HOME control MUST have Tip Action: new (got '${tipAction || 'empty'}'). Robot drops tips when homing.`,
              row: i + 2
            })
          }
        }
      }
    })

    if (validTransfers === 0) {
      newResults.push({ type: 'error', message: 'No valid transfers found in CSV' })
    } else {
      newResults.push({ type: 'valid', message: `${validTransfers} transfer rows found` })
    }

    // Check for distribution + destination mixing incompatibility
    // The Opentrons distribute() API ignores mix_after parameter
    if (hasAnyDistributionRow && state.settings?.settings?.liquid_handling?.mixing?.enabled) {
      const mixingLocation = state.settings.settings.liquid_handling.mixing.location
      if (mixingLocation === 'destination') {
        newResults.push({
          type: 'error',
          message: 'Destination mixing is NOT supported in distribution mode. The distribute() API ignores mix_after. Either disable mixing, change mixing location to "source", or use cherry-pick mode.'
        })
      }
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
