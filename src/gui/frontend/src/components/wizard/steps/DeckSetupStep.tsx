import { useState, useEffect } from 'react'
import { Stack, Alert, Text, Select, Group, Tooltip, ActionIcon, Paper, Title, TextInput, Button } from '@mantine/core'
import { IconAlertCircle, IconHelp, IconDeviceFloppy } from '@tabler/icons-react'
import { DeckGrid } from '../deck/DeckGrid'
import { LabwareEditor } from '../deck/LabwareEditor'
import { useWizard } from '../WizardContext'
import { useSettingsQuery, usePatchSetting, useShellSettingsQuery, useUpdateShellSettings } from '../../../api/hooks'
import { notifications } from '@mantine/notifications'
import { HELP_TEXT } from '../../../constants/helpText'

export function DeckSetupStep() {
  const { state } = useWizard()
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()
  const shellSettingsQuery = useShellSettingsQuery()
  const shellSettingsUpdate = useUpdateShellSettings()

  const [localProtocolName, setLocalProtocolName] = useState('')
  const [opentronsDirWin, setOpentronsDirWin] = useState('')
  const [isSavingOpentrons, setIsSavingOpentrons] = useState(false)

  useEffect(() => {
    setLocalProtocolName(settings?.settings?.general?.protocol_name || '')
  }, [settings?.settings?.general?.protocol_name])

  useEffect(() => {
    if (shellSettingsQuery.data) {
      setOpentronsDirWin(shellSettingsQuery.data.opentrons_dir_win ?? '')
    }
  }, [shellSettingsQuery.data])

  const handleSaveOpentronsDirPath = () => {
    if (!opentronsDirWin) {
      notifications.show({ color: 'red', title: 'Folder required', message: 'Enter the Opentrons App folder path before saving.' })
      return
    }
    const trimmed = opentronsDirWin.replace(/[\\/]+$/, '')
    const looksValid = /[/\\]Opentrons$/i.test(trimmed)
    if (!looksValid) {
      notifications.show({
        color: 'yellow',
        title: 'Path may be incorrect',
        message: 'Expected path ending with "Opentrons" (e.g. C:\\Users\\...\\AppData\\Roaming\\Opentrons). Saving anyway.',
      })
    }
    setIsSavingOpentrons(true)
    shellSettingsUpdate.mutate(
      { opentrons_dir_win: opentronsDirWin },
      {
        onSuccess: () =>
          notifications.show({ color: 'teal', title: 'Opentrons folder saved', message: 'Will be used for simulation and deployment.' }),
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Save failed', message: error instanceof Error ? error.message : 'Unable to save.' }),
        onSettled: () => setIsSavingOpentrons(false),
      }
    )
  }

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
          <Title order={5}>Protocol Name</Title>
          <TextInput
            label={
              <Group gap={4}>
                Custom name for this protocol
                <Tooltip label={HELP_TEXT.protocolName} maw={400} multiline>
                  <ActionIcon size="xs" variant="subtle" color="gray">
                    <IconHelp size={14} />
                  </ActionIcon>
                </Tooltip>
              </Group>
            }
            description="Displayed on the OT-2 touchscreen during execution"
            placeholder="Unified Cherry-Pick & Distribution Protocol"
            value={localProtocolName}
            onChange={(e) => setLocalProtocolName(e.currentTarget.value)}
            onBlur={() => {
              const currentValue = settings?.settings?.general?.protocol_name || ''
              if (localProtocolName !== currentValue) {
                patchMutation.mutate(
                  { path: 'settings.general.protocol_name', value: localProtocolName },
                  {
                    onSuccess: () => {
                      notifications.show({
                        color: 'teal',
                        message: 'Protocol name updated',
                        position: 'top-right',
                      })
                    },
                    onError: (error) => {
                      notifications.show({
                        color: 'red',
                        title: 'Failed to update protocol name',
                        message: error instanceof Error ? error.message : 'Unknown error',
                        position: 'top-right',
                      })
                    },
                  }
                )
              }
            }}
          />
        </Stack>
      </Paper>

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

      <Paper p="md" withBorder>
        <Stack gap="sm">
          <Title order={5}>Opentrons Folder</Title>
          <Text size="sm" c="dimmed">
            Root folder of your Opentrons App installation (contains labware/ and protocols/ subdirectories).
          </Text>
          <TextInput
            label="Opentrons App folder (Windows path)"
            description="Used for custom labware scanning, simulation, and deployment"
            value={opentronsDirWin}
            onChange={(e) => setOpentronsDirWin(e.currentTarget.value)}
            placeholder="C:\Users\...\AppData\Roaming\Opentrons"
          />
          <Button
            variant="light"
            leftSection={<IconDeviceFloppy size={16} />}
            loading={isSavingOpentrons}
            onClick={handleSaveOpentronsDirPath}
          >
            Save as default
          </Button>
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
