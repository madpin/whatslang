import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { useBot, useBotTypes, useCreateBot, useUpdateBot } from '@/hooks/useBots'
import type { BotCreate } from '@/types/bot'

export default function BotForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const { data: bot, isLoading: botLoading } = useBot(id || '')
  const { data: botTypes, isLoading: typesLoading } = useBotTypes()
  const createBot = useCreateBot()
  const updateBot = useUpdateBot()

  const [formData, setFormData] = useState<BotCreate>({
    type: '',
    name: '',
    description: '',
    config: {},
    enabled: true,
  })

  useEffect(() => {
    if (bot && isEdit) {
      setFormData({
        type: bot.type,
        name: bot.name,
        description: bot.description || '',
        config: bot.config,
        enabled: bot.enabled,
      })
    }
  }, [bot, isEdit])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (isEdit && id) {
      updateBot.mutate(
        { id, bot: formData },
        {
          onSuccess: () => navigate('/bots'),
        }
      )
    } else {
      createBot.mutate(formData, {
        onSuccess: () => navigate('/bots'),
      })
    }
  }

  const selectedBotType = botTypes?.find(bt => bt.type === formData.type)
  const configSchema = selectedBotType?.info.config_schema || {}

  const renderConfigField = (key: string, schema: any) => {
    const value = formData.config?.[key] ?? schema.default ?? ''

    switch (schema.type) {
      case 'boolean':
        return (
          <div key={key} className="flex items-center justify-between">
            <Label htmlFor={key}>{schema.title || key}</Label>
            <Switch
              id={key}
              checked={value}
              onCheckedChange={(checked) =>
                setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, [key]: checked }
                }))
              }
            />
          </div>
        )
      case 'array':
        return (
          <div key={key} className="space-y-2">
            <Label htmlFor={key}>{schema.title || key}</Label>
            <Input
              id={key}
              placeholder={schema.description || 'Comma-separated values'}
              value={Array.isArray(value) ? value.join(', ') : ''}
              onChange={(e) =>
                setFormData(prev => ({
                  ...prev,
                  config: {
                    ...prev.config,
                    [key]: e.target.value.split(',').map(v => v.trim()).filter(Boolean)
                  }
                }))
              }
            />
            {schema.description && (
              <p className="text-xs text-muted-foreground">{schema.description}</p>
            )}
          </div>
        )
      default:
        return (
          <div key={key} className="space-y-2">
            <Label htmlFor={key}>{schema.title || key}</Label>
            <Input
              id={key}
              placeholder={schema.description || ''}
              value={value}
              onChange={(e) =>
                setFormData(prev => ({
                  ...prev,
                  config: { ...prev.config, [key]: e.target.value }
                }))
              }
            />
            {schema.description && (
              <p className="text-xs text-muted-foreground">{schema.description}</p>
            )}
          </div>
        )
    }
  }

  if (isEdit && botLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/bots')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">
            {isEdit ? 'Edit Bot' : 'Create Bot'}
          </h1>
          <p className="text-muted-foreground">
            {isEdit ? 'Update your bot configuration' : 'Configure a new bot instance'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Bot Configuration</CardTitle>
            <CardDescription>
              Configure the bot type and settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Bot Type */}
            <div className="space-y-2">
              <Label htmlFor="type">Bot Type *</Label>
              <Select
                id="type"
                value={formData.type}
                onChange={(e) => {
                  setFormData(prev => ({
                    ...prev,
                    type: e.target.value,
                    config: {}
                  }))
                }}
                disabled={isEdit || typesLoading}
                required
              >
                <option value="">Select a bot type</option>
                {botTypes?.map((bt) => (
                  <option key={bt.type} value={bt.type}>
                    {bt.info.name} - {bt.info.description}
                  </option>
                ))}
              </Select>
            </div>

            {/* Bot Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Bot Name *</Label>
              <Input
                id="name"
                placeholder="My Translation Bot"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what this bot does..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={3}
              />
            </div>

            {/* Dynamic Config Fields */}
            {formData.type && Object.keys(configSchema).length > 0 && (
              <div className="space-y-4 pt-4 border-t">
                <h3 className="font-medium">Bot-Specific Configuration</h3>
                {Object.entries(configSchema).map(([key, schema]: [string, any]) =>
                  renderConfigField(key, schema)
                )}
              </div>
            )}

            {/* Enabled */}
            <div className="flex items-center justify-between pt-4 border-t">
              <div>
                <Label htmlFor="enabled">Enable Bot</Label>
                <p className="text-sm text-muted-foreground">
                  Bot will start processing messages immediately
                </p>
              </div>
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData(prev => ({ ...prev, enabled: checked }))
                }
              />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-4">
              <Button
                type="submit"
                disabled={createBot.isPending || updateBot.isPending}
              >
                {isEdit ? 'Update Bot' : 'Create Bot'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/bots')}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}

