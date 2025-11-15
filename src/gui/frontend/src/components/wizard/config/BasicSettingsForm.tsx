import { Select, NumberInput, TextInput, Stack, Group, Tooltip, ActionIcon } from '@mantine/core'
import { IconHelp } from '@tabler/icons-react'
import { HELP_TEXT } from '../../../constants/helpText'
import { useSettingsQuery, usePatchSetting } from '../../../api/hooks'
import { notifications } from '@mantine/notifications'

export function BasicSettingsForm() {
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()

  const handleChange = (path: string, value: any) => {
    patchMutation.mutate(
      { path, value },
      {
        onSuccess: () => {
          notifications.show({
            color: 'teal',
            message: 'Setting updated',
            position: 'top-right'
          })
        },
        onError: (error) => {
          notifications.show({
            color: 'red',
            title: 'Failed to update setting',
            message: error instanceof Error ? error.message : 'Unknown error',
            position: 'top-right'
          })
        }
      }
    )
  }

  return (
    <Stack gap="md">
      <Select
        label={
          <Group gap={4}>
            Pipette Mode
            <Tooltip label={HELP_TEXT.mode.single_X1 + '\n\n' + HELP_TEXT.mode.multi_X1 + '\n\n' + HELP_TEXT.mode.multi} maw={400} multiline>
              <ActionIcon size="xs" variant="subtle" color="gray">
                <IconHelp size={14} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
        data={[
          { value: 'single_X1', label: 'Single Channel (single_X1)' },
          { value: 'multi_X1', label: 'Multi Single-Tip (multi_X1)' },
          { value: 'multi', label: 'Multi Full 8-Tip (multi)' }
        ]}
        value={settings?.settings?.general?.mode || 'single_X1'}
        onChange={(v) => v && handleChange('settings.general.mode', v)}
      />

      <Select
        label={
          <Group gap={4}>
            Tip Reuse Strategy
            <Tooltip label={HELP_TEXT.tipReuse.always + '\n\n' + HELP_TEXT.tipReuse.never + '\n\n' + HELP_TEXT.tipReuse.per_source} maw={400} multiline>
              <ActionIcon size="xs" variant="subtle" color="gray">
                <IconHelp size={14} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
        data={[
          { value: 'always', label: 'Always (One tip for all)' },
          { value: 'never', label: 'Never (New tip each transfer)' },
          { value: 'per_source', label: 'Per Source (New tip per labware)' }
        ]}
        value={settings?.settings?.general?.tip_reuse || 'never'}
        onChange={(v) => v && handleChange('settings.general.tip_reuse', v)}
      />

      <NumberInput
        label={
          <Group gap={4}>
            Head Speed (mm/min)
            <Tooltip label={HELP_TEXT.headSpeed} maw={400} multiline>
              <ActionIcon size="xs" variant="subtle" color="gray">
                <IconHelp size={14} />
              </ActionIcon>
            </Tooltip>
          </Group>
        }
        min={50}
        max={600}
        value={settings?.settings?.general?.head_speed?.speed || 400}
        onChange={(v) => typeof v === 'number' && handleChange('settings.general.head_speed.speed', v)}
      />

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
        value={settings?.settings?.general?.starting_tip_well || 'H1'}
        onChange={(e) => handleChange('settings.general.starting_tip_well', e.target.value)}
        placeholder="H1 or A1"
      />
    </Stack>
  )
}
