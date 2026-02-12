import { useCallback, useState } from 'react'
import {
  Accordion,
  Badge,
  Button,
  Group,
  Modal,
  NumberInput,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Tooltip,
  ActionIcon,
} from '@mantine/core'
import { notifications } from '@mantine/notifications'
import { IconDeviceFloppy, IconHelp } from '@tabler/icons-react'
import { HELP_TEXT } from '../../../constants/helpText'
import { useSettingsQuery, usePatchSetting, useSavePreset } from '../../../api/hooks'
import type { LiquidHandlingPreset } from '../../../api/types'

export function AdvancedSettingsAccordion() {
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()
  const savePresetMutation = useSavePreset()
  const [savePresetOpen, setSavePresetOpen] = useState(false)
  const [presetName, setPresetName] = useState('')

  const lh = settings?.settings?.liquid_handling
  const activePreset = lh?.active_preset || ''

  // Wrapped handleChange that auto-clears the active preset when the user
  // manually changes any liquid handling field while a preset is active.
  const handleChange = useCallback(
    (path: string, value: any) => {
      const isLhField =
        path.startsWith('settings.liquid_handling.') &&
        !path.startsWith('settings.liquid_handling.active_preset') &&
        !path.startsWith('settings.liquid_handling.presets')

      if (isLhField && activePreset) {
        // First clear the active preset, then apply the field change
        patchMutation.mutate(
          { path: 'settings.liquid_handling.active_preset', value: '' },
          {
            onSuccess: () => {
              patchMutation.mutate(
                { path, value },
                {
                  onSuccess: () =>
                    notifications.show({
                      color: 'teal',
                      message: 'Setting updated. Preset cleared.',
                      position: 'top-right',
                    }),
                  onError: (error) =>
                    notifications.show({
                      color: 'red',
                      title: 'Error',
                      message: String(error),
                      position: 'top-right',
                    }),
                },
              )
            },
            onError: (error) =>
              notifications.show({
                color: 'red',
                title: 'Error',
                message: String(error),
                position: 'top-right',
              }),
          },
        )
        return
      }

      patchMutation.mutate(
        { path, value },
        {
          onSuccess: () =>
            notifications.show({
              color: 'teal',
              message: 'Setting updated',
              position: 'top-right',
            }),
          onError: (error) =>
            notifications.show({
              color: 'red',
              title: 'Error',
              message: String(error),
              position: 'top-right',
            }),
        },
      )
    },
    [patchMutation, activePreset],
  )

  // Handle preset selection: apply all preset values to individual LH fields
  const handlePresetSelect = useCallback(
    (presetKey: string | null) => {
      if (!lh || !presetKey) return

      if (presetKey === '__custom__') {
        patchMutation.mutate(
          { path: 'settings.liquid_handling.active_preset', value: '' },
          {
            onSuccess: () =>
              notifications.show({
                color: 'teal',
                message: 'Switched to custom settings.',
                position: 'top-right',
              }),
          },
        )
        return
      }

      const preset = lh.presets?.[presetKey]
      if (!preset) return

      // Set the active preset name, then apply each preset field
      patchMutation.mutate(
        { path: 'settings.liquid_handling.active_preset', value: presetKey },
        {
          onSuccess: () => {
            const patches: Array<{ path: string; value: unknown }> = []
            if (preset.pre_aspirate_contact) {
              for (const [k, v] of Object.entries(preset.pre_aspirate_contact)) {
                patches.push({ path: `settings.liquid_handling.pre_aspirate_contact.${k}`, value: v })
              }
            }
            if (preset.post_aspirate_wick) {
              for (const [k, v] of Object.entries(preset.post_aspirate_wick)) {
                patches.push({ path: `settings.liquid_handling.post_aspirate_wick.${k}`, value: v })
              }
            }
            if (preset.delays) {
              for (const [k, v] of Object.entries(preset.delays)) {
                patches.push({ path: `settings.liquid_handling.delays.${k}`, value: v })
              }
            }
            if (preset.push_out) {
              for (const [k, v] of Object.entries(preset.push_out)) {
                patches.push({ path: `settings.liquid_handling.push_out.${k}`, value: v })
              }
            }
            if (preset.mixing) {
              for (const [k, v] of Object.entries(preset.mixing)) {
                patches.push({ path: `settings.liquid_handling.mixing.${k}`, value: v })
              }
            }

            // Apply patches sequentially
            const applyNext = (idx: number) => {
              if (idx >= patches.length) {
                notifications.show({
                  color: 'teal',
                  title: 'Preset applied',
                  message: `"${presetKey}" preset values loaded.`,
                  position: 'top-right',
                })
                return
              }
              patchMutation.mutate(patches[idx], {
                onSuccess: () => applyNext(idx + 1),
                onError: (error) =>
                  notifications.show({
                    color: 'red',
                    title: 'Error applying preset',
                    message: String(error),
                    position: 'top-right',
                  }),
              })
            }
            applyNext(0)
          },
          onError: (error) =>
            notifications.show({
              color: 'red',
              title: 'Error',
              message: String(error),
              position: 'top-right',
            }),
        },
      )
    },
    [lh, patchMutation],
  )

  // Save current LH values as a named preset
  const handleSavePreset = useCallback(() => {
    if (!lh || !presetName.trim()) return

    const preset: LiquidHandlingPreset = {
      pre_aspirate_contact: { ...lh.pre_aspirate_contact },
      post_aspirate_wick: { ...lh.post_aspirate_wick },
      delays: { ...lh.delays },
      push_out: { ...lh.push_out },
      mixing: { ...lh.mixing },
    }

    savePresetMutation.mutate(
      { name: presetName.trim(), preset },
      {
        onSuccess: () => {
          notifications.show({
            color: 'teal',
            title: 'Preset saved',
            message: `"${presetName.trim()}" has been saved.`,
            position: 'top-right',
          })
          // Set the newly created preset as active
          patchMutation.mutate({
            path: 'settings.liquid_handling.active_preset',
            value: presetName.trim(),
          })
          setSavePresetOpen(false)
          setPresetName('')
        },
        onError: (error) =>
          notifications.show({
            color: 'red',
            title: 'Error saving preset',
            message: String(error),
            position: 'top-right',
          }),
      },
    )
  }, [lh, presetName, savePresetMutation, patchMutation])

  // Build preset selector options from available presets
  const presetOptions = [
    ...(lh?.presets
      ? Object.keys(lh.presets).map((key) => ({
          value: key,
          label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
        }))
      : []),
    { value: '__custom__', label: 'Custom' },
  ]

  const selectedPreset = activePreset || '__custom__'

  return (
    <Stack gap="md">
      {/* Preset Selector - above the accordion */}
      <Group gap="sm" align="flex-end">
        <Select
          label={
            <Group gap={6}>
              <span>Liquid Handling Preset</span>
              {activePreset ? (
                <Badge variant="light" color="blue" size="sm">
                  {activePreset}
                </Badge>
              ) : (
                <Badge variant="light" color="gray" size="sm">
                  Custom
                </Badge>
              )}
            </Group>
          }
          description="Select a preset to apply optimized parameters, or customize below."
          data={presetOptions}
          value={selectedPreset}
          onChange={handlePresetSelect}
          style={{ flex: 1, maxWidth: 350 }}
        />
        <Tooltip label="Save current liquid handling settings as a new preset">
          <Button
            variant="light"
            leftSection={<IconDeviceFloppy size={16} />}
            onClick={() => {
              setPresetName('')
              setSavePresetOpen(true)
            }}
          >
            Save as Preset
          </Button>
        </Tooltip>
      </Group>

      {/* Accordion for individual LH settings */}
      <Accordion variant="separated">
        <Accordion.Item value="pre-aspirate">
          <Accordion.Control>Pre-Aspirate Contact</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <Switch
                label={
                  <Group gap={4}>
                    Enabled
                    <Tooltip label={HELP_TEXT.preAspirateContact.enabled} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                checked={lh?.pre_aspirate_contact?.enabled || false}
                onChange={(e) => handleChange('settings.liquid_handling.pre_aspirate_contact.enabled', e.target.checked)}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Position Offset (%)
                    <Tooltip label={HELP_TEXT.preAspirateContact.positionOffsetPercent} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.pre_aspirate_contact?.position_offset_percent || 20}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.pre_aspirate_contact.position_offset_percent', v)}
                min={0}
                max={100}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Aspirate Volume (uL)
                    <Tooltip label={HELP_TEXT.preAspirateContact.aspirateVolume} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.pre_aspirate_contact?.aspirate_volume || 0}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.pre_aspirate_contact.aspirate_volume', v)}
                min={0}
              />
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value="post-wick">
          <Accordion.Control>Post-Aspirate Wick</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <Switch
                label={
                  <Group gap={4}>
                    Enabled
                    <Tooltip label={HELP_TEXT.postAspirateWick.enabled} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                checked={lh?.post_aspirate_wick?.enabled || false}
                onChange={(e) => handleChange('settings.liquid_handling.post_aspirate_wick.enabled', e.target.checked)}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Radius (fraction of well radius)
                    <Tooltip label={HELP_TEXT.postAspirateWick.radius} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.post_aspirate_wick?.radius || 0.8}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.post_aspirate_wick.radius', v)}
                min={0}
                max={1}
                step={0.1}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Vertical Offset (mm)
                    <Tooltip label={HELP_TEXT.postAspirateWick.vOffsetMm} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.post_aspirate_wick?.v_offset_mm || -1.5}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.post_aspirate_wick.v_offset_mm', v)}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Speed (mm/s)
                    <Tooltip label={HELP_TEXT.postAspirateWick.speed} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.post_aspirate_wick?.speed || 20}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.post_aspirate_wick.speed', v)}
                min={0}
              />
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value="delays">
          <Accordion.Control>Delays & Push-Out</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <NumberInput
                label={
                  <Group gap={4}>
                    Post-Aspirate Delay (seconds)
                    <Tooltip label={HELP_TEXT.delays.postAspirate} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.delays?.post_aspirate || 0}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.delays.post_aspirate', v)}
                min={0}
                step={0.5}
              />

              <Switch
                label={
                  <Group gap={4}>
                    Push-Out Enabled
                    <Tooltip label={HELP_TEXT.pushOut.enabled} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                checked={lh?.push_out?.enabled || false}
                onChange={(e) => handleChange('settings.liquid_handling.push_out.enabled', e.target.checked)}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Push-Out Volume (uL)
                    <Tooltip label={HELP_TEXT.pushOut.volumeUl} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.push_out?.volume_ul || 5}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.push_out.volume_ul', v)}
                min={0}
                max={10}
              />
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value="mixing">
          <Accordion.Control>Mixing Settings</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <Switch
                label={
                  <Group gap={4}>
                    Enabled
                    <Tooltip label={HELP_TEXT.mixing.enabled} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                checked={lh?.mixing?.enabled || false}
                onChange={(e) => handleChange('settings.liquid_handling.mixing.enabled', e.target.checked)}
              />

              <Select
                label={
                  <Group gap={4}>
                    Mixing Location
                    <Tooltip label={HELP_TEXT.mixing.location} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                data={[
                  { value: 'none', label: 'No mixing' },
                  { value: 'source', label: 'Mix at source' },
                  { value: 'destination', label: 'Mix at destination' }
                ]}
                value={lh?.mixing?.location || 'destination'}
                onChange={(v) => v && handleChange('settings.liquid_handling.mixing.location', v)}
                disabled={!lh?.mixing?.enabled}
              />

              <NumberInput
                label={
                  <Group gap={4}>
                    Repetitions
                    <Tooltip label={HELP_TEXT.mixing.repetitions} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                value={lh?.mixing?.repetitions || 0}
                onChange={(v) => typeof v === 'number' && handleChange('settings.liquid_handling.mixing.repetitions', v)}
                min={0}
                max={10}
                disabled={!lh?.mixing?.enabled}
              />

              <Select
                label={
                  <Group gap={4}>
                    Source Remixing
                    <Tooltip label={HELP_TEXT.mixing.sourceRemixing} maw={350} multiline>
                      <ActionIcon size="xs" variant="subtle" color="gray">
                        <IconHelp size={14} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                }
                data={[
                  { value: 'once', label: 'Once (first visit only)' },
                  { value: 'always', label: 'Always (every visit)' }
                ]}
                value={lh?.mixing?.source_remixing || 'once'}
                onChange={(v) => v && handleChange('settings.liquid_handling.mixing.source_remixing', v)}
                disabled={!lh?.mixing?.enabled}
              />
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Save as Preset Modal */}
      <Modal
        opened={savePresetOpen}
        onClose={() => setSavePresetOpen(false)}
        title="Save as Preset"
        centered
      >
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Save the current liquid handling settings as a named preset.
            The preset will be available for future use.
          </Text>
          <TextInput
            label="Preset name"
            placeholder="e.g. my_viscous_preset"
            value={presetName}
            onChange={(event) => setPresetName(event.currentTarget.value)}
            description="Must start with a letter. Only letters, numbers, and underscores allowed."
            error={
              presetName && !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(presetName)
                ? 'Invalid preset name'
                : undefined
            }
          />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setSavePresetOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSavePreset}
              loading={savePresetMutation.isPending}
              disabled={!presetName.trim() || !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(presetName)}
            >
              Save Preset
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  )
}
