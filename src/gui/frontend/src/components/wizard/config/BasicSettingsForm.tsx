import { NumberInput, Stack, Group, Tooltip, ActionIcon } from '@mantine/core'
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
    </Stack>
  )
}
