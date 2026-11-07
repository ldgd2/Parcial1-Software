abstract class BaseDto {
  Map<String, dynamic> toJson();
}

class ApiResponse<T> {
  final bool success;
  final String? message;
  final T? data;
  final List<String>? errors;

  const ApiResponse({
    this.success = true,
    this.message,
    this.data,
    this.errors,
  });

  factory ApiResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic json)? fromJsonT,
  ) {
    final status = json['status'];
    final isSuccess = json['success'] as bool? ?? (status == 'success' || status == 200);
    return ApiResponse<T>(
      success: isSuccess,
      message: json['message'] as String?,
      data: json['data'] != null && fromJsonT != null ? fromJsonT(json['data']) : json['data'] as T?,
      errors: json['errors'] != null ? List<String>.from(json['errors'] as List) : null,
    );
  }
}

class PaginatedResponse<T> {
  final List<T> items;
  final int total;
  final int page;
  final int pageSize;
  final bool hasMore;

  const PaginatedResponse({
    required this.items,
    this.total = 0,
    this.page = 1,
    this.pageSize = 20,
    this.hasMore = false,
  });

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJsonT,
  ) {
    final rawList = json['content'] ?? json['items'] ?? json['data'] ?? [];
    final List<T> list = (rawList as List)
        .map((e) => fromJsonT(Map<String, dynamic>.from(e as Map)))
        .toList();

    final totalElements = (json['totalElements'] ?? json['total'] ?? list.length) as int;
    final currentPage = (json['number'] ?? json['page'] ?? 1) as int;
    final size = (json['size'] ?? json['pageSize'] ?? 20) as int;

    return PaginatedResponse<T>(
      items: list,
      total: totalElements,
      page: currentPage,
      pageSize: size,
      hasMore: totalElements > (currentPage * size),
    );
  }
}

