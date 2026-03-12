import { Body, Controller, Get, Post } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Post('summarize')
  summarize(
    @Body() { videoId }: { videoId: string },
  ): Promise<{ summary: string }> {
    return Promise.resolve({ summary: `Summarizing video ${videoId}...` });
  }
}
