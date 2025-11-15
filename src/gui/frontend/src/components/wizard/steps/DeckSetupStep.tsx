import { Stack, Alert, Text } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { DeckGrid } from '../deck/DeckGrid'
import { useWizard } from '../WizardContext'

export function DeckSetupStep() {
  const { state } = useWizard()

  const hasSource = state.deckLayout.some(l => l.type === 'source')
  const hasDestination = state.deckLayout.some(l => l.type === 'destination')
  const hasTip = state.deckLayout.some(l => l.type === 'tip')
  const hasMinimumLabware = hasSource && hasDestination && hasTip

  return (
    <Stack gap="lg">
      <DeckGrid />

      {!hasMinimumLabware && (
        <Alert
          variant="light"
          color="orange"
          title="Incomplete deck configuration"
          icon={<IconAlertCircle />}
        >
          <Text size="sm">
            To proceed, you need at least:
          </Text>
          <ul style={{ marginTop: 8, marginBottom: 0 }}>
            {!hasSource && <li>1 source labware</li>}
            {!hasDestination && <li>1 destination labware</li>}
            {!hasTip && <li>1 tip rack</li>}
          </ul>
        </Alert>
      )}
    </Stack>
  )
}
