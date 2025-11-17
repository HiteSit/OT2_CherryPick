import { Grid, Stack, Paper, Title, Text, Alert } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import { useEffect } from 'react'
import { BasicSettingsForm } from '../config/BasicSettingsForm'
import { AdvancedSettingsAccordion } from '../config/AdvancedSettingsAccordion'
import { useWizard } from '../WizardContext'
import { useSettingsQuery } from '../../../api/hooks'

export function ConfigurationStep() {
  const { state, setSettings } = useWizard()
  const { data: settings } = useSettingsQuery()

  // Sync settings from API query into wizard context for validation
  // Note: setSettings is a stable Context function and should NOT be in the dependency array
  useEffect(() => {
    if (settings && !state.settings) {
      setSettings(settings)
    }
  }, [settings, state.settings])

  // Context-aware warning for multi mode
  const hasNon96Or384Plate = state.deckLayout.some(labware => {
    // Extract labware_id to check well count from labware definitions
    // This is a simplified check - in production you'd query labware definitions
    const labwareId = labware.labware_id || ''
    // Check if labware type suggests non-96/384 well format
    return labwareId.includes('24') || labwareId.includes('48') || labwareId.includes('tube')
  })

  const showMultiModeWarning = settings?.settings?.general?.mode === 'multi' && hasNon96Or384Plate

  return (
    <Grid>
      <Grid.Col span={7}>
        <Stack>
          {showMultiModeWarning && (
            <Alert color="orange" icon={<IconAlertTriangle size={16} />}>
              Multi mode requires 96 or 384-well plates. Your deck may contain other plate types.
              Verify your labware is compatible before running the protocol.
            </Alert>
          )}

          <Paper withBorder p="md">
            <Title order={4} mb="md">Basic Settings</Title>
            <BasicSettingsForm />
          </Paper>

          <Paper withBorder p="md">
            <Title order={4} mb="md">Advanced Liquid Handling</Title>
            <AdvancedSettingsAccordion />
          </Paper>
        </Stack>
      </Grid.Col>

      <Grid.Col span={5}>
        <Paper withBorder p="md" style={{ position: 'sticky', top: 20 }}>
          <Title order={5} mb="md">Help</Title>
          <Text size="sm" c="dimmed">
            Hover over the <IconAlertTriangle size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> icons next to each setting for detailed explanations.
          </Text>
          <Text size="sm" c="dimmed" mt="md">
            Settings are automatically saved when you make changes and synchronized with the backend.
          </Text>
          <Text size="sm" fw={500} mt="lg">
            Quick Tips:
          </Text>
          <Text size="xs" c="dimmed" mt="xs">
            • Use <strong>single_X1</strong> mode for maximum cherry-picking flexibility
          </Text>
          <Text size="xs" c="dimmed">
            • Enable <strong>Post-Aspirate Wick</strong> to prevent dripping
          </Text>
          <Text size="xs" c="dimmed">
            • Increase <strong>Post-Aspirate Delay</strong> for viscous liquids
          </Text>
          <Text size="xs" c="dimmed">
            • Set <strong>Head Speed</strong> to 200-300 for volatile solvents
          </Text>
        </Paper>
      </Grid.Col>
    </Grid>
  )
}
