import { Accordion, Stack, Switch, NumberInput, Select, Group, Tooltip, ActionIcon } from '@mantine/core'
import { IconHelp } from '@tabler/icons-react'
import { HELP_TEXT } from '../../../constants/helpText'
import { useSettingsQuery, usePatchSetting } from '../../../api/hooks'

export function AdvancedSettingsAccordion() {
  const { data: settings } = useSettingsQuery()
  const patchMutation = usePatchSetting()

  const handleChange = (path: string, value: any) => {
    patchMutation.mutate({ path, value })
  }

  const lh = settings?.settings?.liquid_handling

  return (
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
                  Aspirate Volume (µL)
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
                  Push-Out Volume (µL)
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
              value={lh?.mixing?.location || 'none'}
              onChange={(v) => v && handleChange('settings.liquid_handling.mixing.location', v)}
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
            />
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  )
}
