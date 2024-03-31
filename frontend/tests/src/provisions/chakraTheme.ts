import {
  extendBaseTheme,
  theme as chakraTheme,
} from '@chakra-ui/react'

const { Button, Switch, FormLabel, Radio, Heading, Card } = chakraTheme.components

export const theme = extendBaseTheme({
  components: {
    Button,
    Switch,
    FormLabel,
    Radio,
    Heading,
    Card,
  },
})
