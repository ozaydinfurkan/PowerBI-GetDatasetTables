SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[SemanticModelDetail](
	[ETLDATE] [datetime2](7) NULL,
	[workspace_id] [nvarchar](50) NULL,
	[workspace_name] [nvarchar](255) NULL,
	[dataset_id] [nvarchar](50) NULL,
	[dataset_name] [nvarchar](255) NULL,
	[TableName] [nvarchar](255) NULL,
	[SourceType] [nvarchar](255) NULL,
	[SourceWorkspaceID] [nvarchar](50) NULL,
	[SourceDataflowID] [nvarchar](50) NULL,
	[DataflowURL] [nvarchar](255) NULL,
	[ServerName] [nvarchar](255) NULL,
	[DatabaseName] [nvarchar](255) NULL,
	[DatabaseTableReference] [nvarchar](max) NULL,
	[SharepointURL] [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[SemanticModelDetail] ADD  DEFAULT (getdate()) FOR [ETLDATE]
GO
