I want to create a simple web application that provides a digital badge that is generated and then provided to people to share via linkedin. the design of the architecture is provided in the attached image.

ADMIN

- admin page setups up different badges
- admin page allows new badges to be created using Amazon Bedrock Nova image models
- admin page provides logos and assets that should be used
- admin page should provide layout tools to allow simple moving/editing of the badge
- admin page allows saving of badges as "templates" which is what is used during the creation of a virtual badge
- a default "template" will be defined and used as the default template

FLOW

- a request will come in to create a new virtual badge
- the user will be prompted to enter a name they want displayed
- the user will be asked for confirmation before proceeding
- the request will have a template id that should match a template id in the admin system (if no template id is provided, a default template id is used)
- the system will pass this request to the badge generation system, and treat this as a immutable request
- the badge generation system will create a unique record for this virtual badge and generate the virtual badge link
- the system will used the resources available (created/managed by the admin system)
- the sysem will host this virtual badge so that it has a unique uri and can be access over http
- the link to the virtual badge is provided back to the requestor as a QR code
- the link to the virtual badge also provides a "share in linkedin" button which will share the virtual badge link

ACCESSING BADGES

- virtual badges are available via their public uri

TECH

- use strands agents when using generative AI and to access Nova models
- use us-east-1 or us-west-2 for regions as these have access to the Nova models
- use the strands agent MCP Server to get the latest info on Strands Agent
- use bootstrap for the web app ui

