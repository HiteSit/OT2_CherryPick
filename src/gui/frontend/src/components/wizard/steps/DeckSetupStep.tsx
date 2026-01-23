import { Stack, Alert, Text, Select, Group, Tooltip, ActionIcon, Paper, Title, TextInput } from '@mantine/core'
import { IconAlertCircle, IconHelp } from '@tabler/icons-react'
import { DeckGrid } from '../deck/DeckGrid'
import { LabwareEditor } from '../deck/LabwareEditor'
import { useWizard } from '../WizardContext'
import { useSettingsQuery, usePatchSetting } from '../../../api/hooks'
import { notifications } from '@mantine/notifications'
import { HELP_TEXT } from '../../../constants/helpText'

export function DeckSetupStep() {
  const { state } = useWizard()
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()

  const hasSource = state.deckLayout.some(l => l.type === 'source')
  const hasDestination = state.deckLayout.some(l => l.type === 'destination')
  const hasTip = state.deckLayout.some(l => l.type === 'tip')
  const hasMinimumLabware = hasSource && hasDestination && hasTip

  const handleModeChange = (value: string | null) => {
    if (value) {
      patchMutation.mutate(
        { path: 'settings.general.mode', value },
        {
          onSuccess: () => {
            notifications.show({
              color: 'teal',
              message: 'Pipette mode updated',
              position: 'top-right'
            })
          },
          onError: (error) => {
            notifications.show({
              color: 'red',
              title: 'Failed to update mode',
              message: error instanceof Error ? error.message : 'Unknown error',
              position: 'top-right'
            })
          }
        }
      )
    }
  }

  const currentMode = settings?.settings?.general?.mode || 'single_X1'
  const isDualMode = currentMode === 'dual'
  const isMultiX1Mode = currentMode === 'multi_X1'

  const handleStartingTipWellChange = (value: string) => {
    patchMutation.mutate(
      { path: 'settings.general.starting_tip_well', value },
      {
        onSuccess: () => {
          notifications.show({
            color: 'teal',
            message: 'Starting tip well updated',
            position: 'top-right'
          })
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: 'Failed to update starting tip well',
            message: error instanceof Error ? error.message : 'Unknown error',
            position: 'top-right'
          })
        }
      }
    )
  }

  return (
    <Stack gap="lg">
      <Paper p="md" withBorder>
        <Stack gap="sm">
          <Title order={5}>Pipette Mode</Title>
          <Select
            label={
              <Group gap={4}>
                Select pipette mode before configuring tip racks
                <Tooltip label={HELP_TEXT.mode.single_X1 + '\n\n' + HELP_TEXT.mode.multi_X1 + '\n\n' + HELP_TEXT.mode.multi + '\n\n' + HELP_TEXT.mode.dual} maw={400} multiline>
                  <ActionIcon size="xs" variant="subtle" color="gray">
                    <IconHelp size={14} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            }
            data={[
              { value: 'single_X1', label: 'Single Channel (single_X1)' },
              { value: 'multi_X1', label: 'Multi Single-Tip (multi_X1)' },
              { value: 'multi', label: 'Multi Full 8-Tip (multi)' },
              { value: 'dual', label: 'Dual Pipette (dual)' }
            ]}
            value={currentMode}
            onChange={handleModeChange}
          />
          {isDualMode && (
            <Alert color="blue" variant="light">
              <Text size="sm">
                <strong>Dual mode enabled:</strong> When adding tip racks, you must specify which transfer mode (multi, multi_X1, single_X1) each tip rack is assigned to.
              </Text>
            </Alert>
          )}
          {isMultiX1Mode && (
            <TextInput
              label={
                <Group gap={4}>
                  Starting Tip Well
                  <Tooltip label={HELP_TEXT.startingTipWell} maw={400} multiline>
                    <ActionIcon size="xs" variant="subtle" color="gray">
                      <IconHelp size={14} />
                    </ActionIcon>
                  </Tooltip>
                </Group>
              }
              description="Nozzle position for single-tip mode (e.g., H1 for bottom nozzle)"
              value={settings?.settings?.general?.starting_tip_well || 'H1'}
              onChange={(e) => handleStartingTipWellChange(e.target.value)}
              placeholder="H1 or A1"
            />
          )}
        </Stack>
      </Paper>

      <DeckGrid />

      <LabwareEditor />

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
