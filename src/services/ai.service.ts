// export const generateSlideExplanations = async (
//   s3Url: string, 
//   companyName: string,
//   tenantDetails: TenantDetails
// ): Promise<SlideExplanation[]> => {
//   try {
//     console.log('Generating explanations for:', { s3Url, companyName, tenantDetails });
    
//     // Validate S3 URL
//     if (!s3Url) {
//       console.error('Invalid S3 URL:', s3Url);
//       throw new Error('Invalid S3 URL provided');
//     }

//     // Format S3 URL to ensure it matches the required format
//     let formattedS3Url = s3Url;
//     if (s3Url.startsWith('https://')) {
//       const url = new URL(s3Url);
//       const pathParts = url.pathname.split('/');
//       const filename = pathParts.pop();
//       const encodedFilename = encodeURIComponent(filename || '');
//       formattedS3Url = `https://${url.hostname}${pathParts.join('/')}/${encodedFilename}`;
//     } else if (s3Url.startsWith('s3://')) {
//       const [bucket, ...keyParts] = s3Url.replace('s3://', '').split('/');
//       const key = keyParts.join('/');
//       formattedS3Url = `https://${bucket}.s3.amazonaws.com/${encodeURIComponent(key)}`;
//     }

//     formattedS3Url = formattedS3Url.replace(/%2B/g, '+');
//     formattedS3Url = formattedS3Url.replace(/%20/g, '+');

//     console.log('Formatted S3 URL:', formattedS3Url);

//     // Make sure to include tenant_details in the request body
//     const requestBody = {
//       s3_url: formattedS3Url,
//       company_name: companyName,
//       tenant_details: {
//         presidingOfficerEmail: tenantDetails.presidingOfficerEmail,
//         poshCommitteeEmail: tenantDetails.poshCommitteeEmail,
//         hrContactName: tenantDetails.hrContactName,
//         hrContactEmail: tenantDetails.hrContactEmail,
//         hrContactPhone: tenantDetails.hrContactPhone,
//         ceoName: tenantDetails.ceoName,
//         ceoEmail: tenantDetails.ceoEmail,
//         ceoContact: tenantDetails.ceoContact,
//         ctoName: tenantDetails.ctoName,
//         ctoEmail: tenantDetails.ctoEmail,
//         ctoContact: tenantDetails.ctoContact,
//         ccoEmail: tenantDetails.ccoEmail,
//         ccoContact: tenantDetails.ccoContact,
//         croName: tenantDetails.croName,
//         croEmail: tenantDetails.croEmail,
//         croContact: tenantDetails.croContact,
//         legalOfficerName: tenantDetails.legalOfficerName,
//         legalOfficerEmail: tenantDetails.legalOfficerEmail,
//         legalOfficerContact: tenantDetails.legalOfficerContact
//       }
//     };

//     console.log('Sending request to AI service:', {
//       url: `${process.env.AI_SERVICE_URL}/generate_explanations`,
//       body: requestBody
//     });

//     const response = await aiServiceClient.post('/generate_explanations', requestBody);

//     console.log('AI service response:', {
//       status: response.status,
//       statusText: response.statusText,
//       data: response.data
//     });

//     if (!response.data || !Array.isArray(response.data.explanations)) {
//       console.error('Invalid response format from AI service:', response.data);
//       throw new Error('Invalid response format from AI service');
//     }

//     return response.data.explanations;
//   } catch (error) {
//     console.error('Error generating slide explanations:', error);
//     if (axios.isAxiosError(error)) {
//       console.error('AI Service Error Details:', {
//         status: error.response?.status,
//         statusText: error.response?.statusText,
//         data: error.response?.data,
//         url: error.config?.url,
//         method: error.config?.method,
//         headers: error.config?.headers,
//         baseURL: error.config?.baseURL
//       });
//       throw new Error(`AI Service Error: ${error.response?.status} ${error.response?.statusText} - ${JSON.stringify(error.response?.data)}`);
//     }
//     throw new Error('Failed to generate slide explanations: ' + (error instanceof Error ? error.message : 'Unknown error'));
//   }
// }; 