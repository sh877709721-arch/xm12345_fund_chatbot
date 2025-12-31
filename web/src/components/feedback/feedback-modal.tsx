import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Upload, MessageCircle, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadFeedbackImage, submitFeedback, type FeedbackImage } from "@/utils/request/feedback";

interface ImageFile {
  file: File;
  preview: string;
  id: string;
}

interface FeedbackModalProps {
  trigger?: React.ReactNode;
  className?: string;
}

export const FeedbackModal = ({ trigger, className }: FeedbackModalProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [content, setContent] = useState("");
  const [phone, setPhone] = useState("");
  const [images, setImages] = useState<ImageFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    const newImages: ImageFile[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // 验证文件类型
      const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"];
      if (!allowedTypes.includes(file.type)) {
        alert(`不支持的文件类型: ${file.name}。支持的格式: JPEG, PNG, GIF, WebP`);
        continue;
      }

      // 验证文件大小 (5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert(`文件过大: ${file.name}。最大允许 5MB`);
        continue;
      }

      const preview = URL.createObjectURL(file);
      newImages.push({
        file,
        preview,
        id: Math.random().toString(36).substr(2, 9),
      });
    }

    setImages(prev => [...prev, ...newImages].slice(0, 5)); // 最多5张图片
  };

  // const removeImage = (id: string) => {
  //   setImages(prev => {
  //     const imageToRemove = prev.find(img => img.id === id);
  //     if (imageToRemove) {
  //       URL.revokeObjectURL(imageToRemove.preview);
  //     }
  //     return prev.filter(img => img.id !== id);
  //   });
  // };

  const uploadImages = async (): Promise<FeedbackImage[]> => {
    const uploadPromises = images.map(async (imageFile) => {
      const result = await uploadFeedbackImage(imageFile.file);
      return {
        url: result.data.url,
        filename: '',
        size: 0,
        content_type: '',
        path: result.data.url
      };
    });

    return Promise.all(uploadPromises);
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      alert('请填写反馈内容');
      return;
    }

    setIsSubmitting(true);
    try {
      let uploadedImages: FeedbackImage[] = [];

      // 如果有图片，先上传
      if (images.length > 0) {
        uploadedImages = await uploadImages();
      }

      // 提交反馈
      await submitFeedback({
        content: content.trim(),
        phone: phone.trim() || undefined,
        images: uploadedImages.length > 0 ? uploadedImages : undefined,
      });

      // 成功后重置表单
      setContent('');
      setPhone('');
      setImages([]);
      setIsOpen(false);

    } catch (error) {
      console.error('提交留言失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // 清理图片预览
    images.forEach(img => URL.revokeObjectURL(img.preview));
    setImages([]);
    setContent('');
    setPhone('');
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button
            variant="outline"
            size="sm"
            className={cn("gap-2", className)}
          >
            <MessageCircle className="h-4 w-4" />
            留言反馈
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>留言反馈</DialogTitle>
          <DialogDescription>
            说说你的问题
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">

          {/* 内容 */}
          <div className="space-y-2">
            <Label htmlFor="content">反馈内容 *</Label>
            <Textarea
              id="content"
              placeholder="请详细描述您的问题或建议..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[120px]"
              maxLength={2000}
            />
          </div>

          {/* 联系电话 */}
          <div className="space-y-2">
            <Label htmlFor="phone">联系电话</Label>
            <Input
              id="phone"
              placeholder="请输入您的联系电话（选填）"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          {/* 图片上传 */}
          <div className="space-y-2 hidden">
            <Label>相关截图（选填，最多5张，每张不超过5MB）</Label>

            {/* 上传按钮 */}
            <div className="flex items-center gap-2">
              <label htmlFor="image-upload">
                <div className="inline-flex items-center gap-2 cursor-pointer">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    asChild
                    disabled={images.length >= 5}
                  >
                    <span>
                      <Upload className="h-4 w-4" />
                      选择图片
                    </span>
                  </Button>
                  <input
                    id="image-upload"
                    type="file"
                    multiple
                    accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={images.length >= 5}
                  />
                </div>
              </label>
              <span className="text-sm text-muted-foreground">
                {images.length}/5
              </span>
            </div>

            {/* 图片预览 
            {images.length > 0 && (
              <div className="grid grid-cols-3 gap-2">
                {images.map((image) => (
                  <div
                    key={image.id}
                    className="relative group border rounded-lg overflow-hidden"
                  >
                    <img
                      src={image.preview}
                      alt="预览"
                      className="w-full h-24 object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => removeImage(image.id)}
                      className="absolute top-1 right-1 bg-black/50 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}*/}
          </div>
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!content.trim() || isSubmitting}
          >
            {isSubmitting ? (
              <>
                <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                提交中...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                提交留言
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};