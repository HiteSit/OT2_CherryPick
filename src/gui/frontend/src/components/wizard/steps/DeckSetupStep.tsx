import { useState, useEffect } from 'react'
import { Stack, Alert, Text, Select, Group, Tooltip, ActionIcon, Paper, Title, TextInput, Button } from '@mantine/core'
import { IconAlertCircle, IconHelp, IconFolder, IconDeviceFloppy } from '@tabler/icons-react'
import { DeckGrid } from '../deck/DeckGrid'
import { LabwareEditor } from '../deck/LabwareEditor'
import { useWizard } from '../WizardContext'
import { useSettingsQuery, usePatchSetting, useShellSettingsQuery, useUpdateShellSettings, useBrowseShellSettings } from '../../../api/hooks'
import { notifications } from '@mantine/notifications'
import { HELP_TEXT } from '../../../constants/helpText'

export function DeckSetupStep() {
  const { state } = useWizard()
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()
  const shellSettingsQuery = useShellSettingsQuery()
  const shellSettingsUpdate = useUpdateShellSettings()
  const shellSettingsBrowse = useBrowseShellSettings()

  const [localProtocolName, setLocalProtocolName] = useState('')
  const [labwarePathWin, setLabwarePathWin] = useState('')
  const [isBrowsingLabware, setIsBrowsingLabware] = useState(false)
  const [isSavingLabware, setIsSavingLabware] = useState(false)

  useEffect(() => {
    setLocalProtocolName(settings?.settings?.general?.protocol_name || '')
  }, [settings?.settings?.general?.protocol_name])

  useEffect(() => {
    if (shellSettingsQuery.data) {
      setLabwarePathWin(shellSettingsQuery.data.labware_path_win ?? '')
    }
  }, [shellSettingsQuery.data])

  const handleBrowseLabwarePath = () => {
    setIsBrowsingLabware(true)
    shellSettingsBrowse.mutate(
      { field: 'labware_path_win' },
      {
        onSuccess: (data) => {
          setLabwarePathWin(data.labware_path_win ?? '')
          notifications.show({ color: 'teal', title: 'Folder selected', message: 'Custom labware folder updated.' })
        },
        onError: (error) =>
          notifications.show({
            color: 'red',
            title: 'Browse failed',
            message: error instanceof Error ? error.message : 'Unable to open folder picker.',
          }),
        onSettled: () => setIsBrowsingLabware(false),
      }
    )
  }

  const handleSaveLabwarePath = () => {
    if (!labwarePathWin) {
      notifications.show({ color: 'red', title: 'Folder required', message: 'Enter a custom labware folder path before saving.' })
      return
    }
    setIsSavingLabware(true)
    shellSettingsUpdate.mutate(
      { labware_path_win: labwarePathWin },
      {
        onSuccess: () =>
          notifications.show({ color: 'teal', title: 'Labware path saved', message: 'Will be used for simulation and scanning.' }),
        onError: (error) =>
          notifications.show({ color: 'red', title: 'Save failed', message: error instanceof Error ? error.message : 'Unable to save.' }),
        onSettled: () => setIsSavingLabware(false),
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
          <Title order={5}>Custom Labware Folder</Title>
          <Text size="sm" c="dimmed">
            Point to your Opentrons custom labware JSON folder. Custom labware will appear first in the labware selector when adding deck slots.
          </Text>
          <TextInput
            label="Custom labware folder (Windows path)"
            description="Example: C:\\Users\\you\\AppData\\Roaming\\Opentrons\\labware"
            value={labwarePathWin}
            onChange={(e) => setLabwarePathWin(e.currentTarget.value)}
            placeholder="C:\\Users\\..."
          />
          <Group gap="xs">
            <Button
              variant="default"
              leftSection={<IconFolder size={16} />}
              loading={isBrowsingLabware}
              onClick={handleBrowseLabwarePath}
            >
              Browse…
            </Button>
            <Button
              variant="light"
              leftSection={<IconDeviceFloppy size={16} />}
              loading={isSavingLabware}
              onClick={handleSaveLabwarePath}
            >
              Save as default
            </Button>
          </Group>
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
